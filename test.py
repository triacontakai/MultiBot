import asyncio
import osu
from osu import bancho

class TestClient(osu.GameClient):
    channel: str

    def __init__(self, username, password):
        super().__init__(username, password)
        self.channel = None

    async def on_init(self):
        await self.privmsg(bancho, '!mp make testing bot, join at own risk')
    async def on_shutdown(self):
        await self.privmsg(self.channel, '!mp close')
    async def on_lobby(self, channel):
        self.channel = channel
        print(f"joined lobby: {channel}")
        await self.privmsg(channel, '!mp password')
    async def on_join(self, channel, player):
        print(f"({channel}) {player} joined")
    async def on_leave(self, channel, player):
        print(f"({channel}) {player} left")
    async def on_chat(self, channel, player, message):
        print(f"({channel}) {player}: {message}")
    async def on_ready(self, channel):
        print(f"({channel}) all players ready!")
    async def on_match_start(self, channel):
        print(f"({channel}) match started")
    async def on_match_end(self, channel):
        print(f"({channel}) match ended")
    async def on_host_new(self, channel, player):
        print(f"({channel}) {player} became the host")
    async def on_host_choosing(self, channel):
        print(f"({channel}) host is choosing a map...")
    async def on_beatmap_change(self, channel, beatmap_name, beatmap_id):
        print(f"({channel}) beatmap changed to {beatmap_name!r} (ID: {beatmap_id})")
