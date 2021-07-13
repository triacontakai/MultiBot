import asyncio
import typing
from dataclasses import dataclass, InitVar, field

# abstracts irc messages into a more easily dealt with form
# also filters out certain types of messages we don't care about (e.g. QUIT)
class IrcHandler:
    username: str
    password: str
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *a):
        self.writer.close()
        await self.writer.wait_closed()

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    # send credentials to irc server in plaintext (yay security)
    async def login(self, username: str, password: str):
        if self.reader is None and self.writer is None:
            self.connect()

        commands = f'PASS {password}'.encode('ascii') + b'\r\n'
        commands += f'USER {username}'.encode('ascii') + b'\r\n'
        commands += f'NICK {username}'.encode('ascii') + b'\r\n'
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

            # if we get a direct IRC command, handle it here
            command, _, argument = response.partition(b' ')
            if response.startswith(b'PING'):
                reply = b'PONG ' + argument + b'\r\n'
                self.writer.write(reply)
                await self.writer.drain()
                print(response)
                print(reply)
            else:
                raise UnsupportedCommandError("Invalid command: {command.decode('ascii')}")

    # sends a message to a client using PRIVMSG
    # works for both channels (prefixed with #) and users
    #async def send_msg(self, who, message):
    #    command = 

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
        blocks = response.split(b':')
        self.data = blocks[1].decode('ascii')

        blocks = blocks[0].split(b' ')
        self.sender = blocks[0].decode('ascii')
        self.command = blocks[1].decode('ascii')
        self.params = [blocks[i].decode('ascii') for i in range(2, len(blocks))]

class UnsupportedCommandError(Exception):
    pass
