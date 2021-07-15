import asyncio
import typing
from typing import Any, Callable, Awaitable
from dataclasses import dataclass, InitVar, field

"""
events:
on_init: called after login
on_shutdown: called right before closing asyncio sockets (in clean shutdown)
on_message: called when IRC command is received from server
"""
class Client:
    host: str
    port: int
    username: str # we store this so we can identify DMs
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    event_exception: Exception

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.username = None
        self.event_exception = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def login(self, username: str, password: str):
        self.username = username

        commands = f'PASS {password}\r\n'.encode('ascii')
        commands += f'USER {username}\r\n'.encode('ascii')
        commands += f'NICK {username}\r\n'.encode('ascii')

        self.writer.write(commands)
        await self.writer.drain()

    async def privmsg(self, who: str, message: str):
        command = f'PRIVMSG {who} :{message}\r\n'.encode('ascii')
        self.writer.write(command)
        await self.writer.drain()

    # attempt to cleanly close IRC connection
    async def close(self):
        self.writer.write(b'QUIT\r\n')
        self.writer.close()
        await self.writer.wait_closed()

    # decorator: registers an event without inheritance
    def event(self, handler: Callable[[Any], Awaitable]) -> Callable:
        bound = handler.__get__(self)
        setattr(self, handler.__name__, bound)
        return handler

    # wrapper around create_task that allows recv loop to handle errors
    # used to avoid "exception was never retreived" warning
    def _handle_task(self, coroutine):
        async def wrapper():
            try:
                await coroutine
            except Exception as e:
                self.event_exception = e

        asyncio.create_task(wrapper())

    # events (to be implemented by client)
    # most of these are executed using create_task in order to prevent blocking _recv_loop
    async def on_init(self) -> None:
        pass
    async def on_shutdown(self) -> None:
        pass
    async def on_message(self, message: 'Message') -> None:
        pass

    # execute full lifecycle of client
    async def start(self, username: str, password: str) -> None:
        try:
            await self.connect()
            await self.login(username, password)
            self._handle_task(self.on_init())
            await self._recv_loop()
        finally:
            # this is the only event we await, since we don't want to close and then shut down
            await self.on_shutdown()
            await self.close()

    # synchronous wrapper for start
    def run(self, username: str, password: str) -> None:
        asyncio.run(self.start(username, password))

    # receive messages indefinitely
    # dispatch registered events as needed
    async def _recv_loop(self) -> None:
        while self.event_exception == None:
            message = await self._recv()
            self._handle_task(self.on_message(message))

        # if we got here an event handler errored, so we're raising this where it will shut down the program
        raise self.event_exception

    # receive a Message from a client and handle IRC commands if we get them
    async def _recv(self) -> 'Message':
        is_command = True
        while is_command:
            response = await self.reader.readline()
            response = response.strip(b'\r\n')
            if response[0] == ord(':'):
                is_command = False
            else:
                await self._handle(response)
                is_command = True

        return Message(response)

    # handle actual IRC commands (not responses)
    async def _handle(self, packet: str) -> None:
        command, argument_str = packet.split(b' ', 1)
        if command == b'PING':
            reply = b'PONG ' + argument_str + b'\r\n'
            self.writer.write(reply)
            await self.writer.drain()
        else:
            raise UnsupportedCommandError("Invalid command: {command.decode('ascii')}")

        

@dataclass
class Message:
    response: InitVar[str]
    sender: str = field(init=False)
    command: str = field(init=False)
    params: list[str] = field(init=False)
    data: str = field(init=False)

    def __post_init__(self, response: str):
        # all responses passed here should start with :
        assert response[0] == ord(':')

        response = response[1:]
        blocks = response.split(b':',1)
        if len(blocks) > 1:
            self.data = blocks[1].decode('ascii')
        else:
            self.data = ''

        blocks = blocks[0].split()
        self.sender = blocks[0].decode('ascii')
        self.command = blocks[1].decode('ascii')
        self.params = [blocks[i].decode('ascii') for i in range(2, len(blocks))]

class UnsupportedCommandError(Exception):
    pass
