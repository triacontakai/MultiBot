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
class IRCManager:
    host: str
    port: int
    username: str # we store this so we can identify DMs
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.username = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def login(self, username: str, password: str):
        self.username = username

        commands = f'PASS {password}\r\n'.encode('ascii')
        commands += f'USER {username}\r\n'.encode('ascii')
        commands += f'NICK {username}\r\n'.encode('ascii')

        self.writer.write(commands)
        await self.writer.drain()

    # attempt to cleanly close connection with QUIT command
    async def close(self):
        self.writer.write(b'QUIT\r\n')
        self.writer.close()
        await self.writer.wait_closed()

    # decorator that registers an event without inheritance
    def event(self, handler: Callable[[Any], Awaitable]) -> Callable:
        bound = handler.__get__(self)
        setattr(self, handler.__name__, bound)
        return handler

    # events (to be implemented by client)
    # these are all executed using create_task in order to prevent blocking _recv_loop
    async def on_init(self) -> None:
        pass
    async def on_shutdown(self) -> None:
        pass
    async def on_message(self, message: 'Message') -> None:
        pass

    # connect, login, and receive messages indefinitely
    # dispatch registered events as needed
    # this also handles cleanup 
    async def _recv_loop(self, username: str, password: str) -> None:
        await self.connect()
        await self.login(username, password)
        asyncio.create_task(self.on_init())
        try:
            while True:
                message = await self._recv()
                asyncio.create_task(self.on_message(message))
        finally:
            await self.on_shutdown()
            await self.close()

    # receive a Message from a client and handle IRC commands if we get them
    async def _recv(self) -> 'Message':
        is_command = True
        while is_command:
            response = await self.reader.readline()
            response = response.strip(b'\r\n')
            if response[0] == ord(':'):
                is_command = False
            else:
                self._handle(response)
                is_command = True

        return Message(response)

    # handle 
    async def _handle(self, packet: str) -> None:
        command, argument_str = response.split(b' ', 1)
        if command == b'PING':
            reply = b'PONG ' + argument_str + b'\r\n'
            self.writer.write(reply)
            await self.writer.drain()
        else:
            raise UnsupportedCommandError("Invalid command: {command.decode('ascii')}")

    def run(self, username: str, password: str) -> None:
        asyncio.run(self._recv_loop(username, password))

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
