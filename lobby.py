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

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *a):
        await self.shutdown()

    # create a lobby and start tracking its state
    async def start(self):
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

    # process next irc message, changing internal state
    async def process_msg(self):
        msg = await self.client.recv_msg()

        # any other commands are likely irc filler
        if msg.command != 'PRIVMSG':
            return

        # only handle messages in DMs or lobby
        msg_channel = msg.params[0]
        if msg_channel != self.channel and msg_channel != self.username:
            return

        # bancho messages will result in lobby state changes, handle this in internal function
        #if msg.sender == f'{bancho}{suffix}' and msg_channel == self.channel:
        #    self._handle_bancho(msg)

        # check player messages for attempt to relay !mp commands
        # TODO: only relay from current host and specified operators
        if msg.data.startswith('!mp'):
            await self.client.privmsg(self.channel, msg.data)
