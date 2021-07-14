import asyncio
import typing
from dataclasses import dataclass, InitVar, field

# abstracts irc messages into a more easily dealt with form
# also filters out certain types of messages we don't care about (e.g. QUIT)
class IrcHandler:
    host: str
    port: int
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *a):
        await self.shutdown()

    async def shutdown(self):
        self.writer.write(b'QUIT\r\n')
        self.writer.close()
        await self.writer.wait_closed()

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    # send credentials to irc server in plaintext (yay security)
    async def login(self, username: str, password: str):
        if self.reader is None and self.writer is None:
            self.connect()

        commands = f'PASS {password}\r\n'.encode('ascii')
        commands += f'USER {username}\r\n'.encode('ascii')
        commands += f'NICK {username}\r\n'.encode('ascii')
        self.writer.write(commands)
        await self.writer.drain()

    # this is where the majority of time will be spent
    # returns a message object
    async def recv_msg(self) -> bytes:
        # we return from this loop as soon as we get a proper message
        while True:
            response = await self.reader.readline()
            response = response.strip(b'\r\n')
            if response[0] == ord(':'):
                return Message(response)

            # if we get an internal IRC command, handle it here
            command, _, argument = response.partition(b' ')
            if command == b'PING':
                reply = b'PONG ' + argument + b'\r\n'
                self.writer.write(reply)
                await self.writer.drain()
            else:
                raise UnsupportedCommandError("Invalid command: {command.decode('ascii')}")

    # sends a private message to a client using PRIVMSG
    # works for both channels (prefixed with #) and users
    async def privmsg(self, who: str, message: str):
        command = f'PRIVMSG {who} :{message}\r\n'.encode('ascii')
        self.writer.write(command)
        await self.writer.drain()

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
        self.data = blocks[1].decode('ascii')

        blocks = blocks[0].split()
        self.sender = blocks[0].decode('ascii')
        self.command = blocks[1].decode('ascii')
        self.params = [blocks[i].decode('ascii') for i in range(2, len(blocks))]

class UnsupportedCommandError(Exception):
    pass
