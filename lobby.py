import re
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
        self.host_queue = list()

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

        if msg.command != 'PRIVMSG':
            return

        msg_channel = msg.params[0]
        if msg_channel != self.channel and msg_channel != self.username:
            return

        # bancho messages will result in lobby state changes, handle this in internal function
        if msg.sender == f'{bancho}{suffix}' and msg_channel == self.channel:
            await self._handle_bancho(msg)

        # check player messages for attempt to relay !mp commands
        # TODO: only relay from current host and specified operators
        if msg.data.startswith('!mp') and msg.sender != self.username:
            await self.client.privmsg(self.channel, msg.data)

    async def _handle_bancho(self, msg):
        # player joining
        if match := re.match(r"(.+) joined in slot \d+.", msg.data):
            name = match.group(1)
            if len(self.host_queue) < 1:
                await self.client.privmsg(self.channel, f'!mp host {name}')

            # we don't want the current host to go twice in a row if there's just one
            if len(self.host_queue) == 1:
                self.host_queue.insert(0, name)
            else:
                self.host_queue.append(name)
            print(f"Player joined! Current host queue: {self.host_queue}")

        # player leaving
        elif match := re.match(r"(.+) left the game.", msg.data):
            name = match.group(1)
            self.host_queue.remove(name)
            print(f"Player left! Current host queue: {self.host_queue}")

        # match ended (time to rotate host)
        elif msg.data == 'The match has finished!':
            print(f"Match ended! Rotating host...")
            name = self.host_queue.pop(0)
            self.host_queue.append(name)
            print(f"New host is {name}")
            print(f"New queue: {self.host_queue}")
            await self.client.privmsg(self.channel, f'!mp host {name}')
            await self.client.privmsg(self.channel, f'Host queue: {self.host_queue}')
