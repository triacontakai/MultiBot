import asyncio
import typing
from connector import IrcHandler

bancho = 'BanchoBot'
suffix = '!cho@ppy.sh'

class LobbyManager:
    client: IrcHandler
    name: str
    channel: str = None
    host_queue: list[str]

    def __init__(self, client: IrcHandler, username: str, lobbyname: str,):
        self.client = client
        self.username = username
        self.lobbyname = lobbyname

    # create a lobby and start tracking its state
    async def lobby(self):
        client = self.client
        await client.privmsg(bancho, f'!mp make {self.lobbyname}')

        # get irc channel from JOIN message
        while self.channel is None:
            msg = await client.recv_msg()
            if msg.command == 'JOIN' and msg.sender == f'{self.username}{suffix}':
                self.channel = msg.data 

        # initial settings
        # TODO: add config for this stuff later
        await client.privmsg(self.channel, '!mp password')

    # we don't close the socket here, that's handled outside
    async def shutdown(self):
        await self.client.privmsg(self.channel, '!mp close')

    async def __aenter__(self):
        await self.lobby()
        return self

    async def __aexit__(self, *a):
        await self.shutdown()
