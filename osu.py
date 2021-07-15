import asyncio
import typing
import irc
import re

# usernames are appended with this
suffix = '!cho@ppy.sh'
bancho = 'BanchoBot'

# TODO: test if on_room is called when bot is dm'd
"""
extension of irc.Client that adds events relevant to osu!
events:
on_lobby: client joins a channel (multi lobby)
on_join: player joins the room
on_leave: player leaves the room
on_chat: non-bancho chat message from another player is received
on_ready: all players readied up
on_match_start: match started
on_match_end: match ended
on_host_new: different player is host
on_host_choosing: host is choosing a beat map
on_beatmap_change: active beatmap updated
"""
class GameClient(irc.Client):
    async def on_lobby(self, channel: str) -> None:
        pass
    async def on_join(self, channel: str, player: str) -> None:
        pass
    async def on_leave(self, channel: str, player: str) -> None:
        pass
    async def on_chat(self, channel: str, player: str, message: str) -> None:
        pass
    async def on_ready(self, channel: str) -> None:
        pass
    async def on_match_start(self, channel:str) -> None:
        pass
    async def on_match_end(self, channel: str) -> None:
        pass
    async def on_host_new(self, channel: str, player: str) -> None:
        pass
    async def on_host_choosing(self, channel: str) -> None:
        pass
    async def on_beatmap_change(self, channel: str, beatmap_name: str, beatmap_id: str) -> None:
        pass

    # parse message and trigger more specific event
    async def on_message(self, message: irc.Message) -> None:
        # don't remove the suffix yet, sometimes the server can directly send a message
        if message.command == 'JOIN' and message.sender == f'{self.username}{suffix}':
            await self.on_lobby(message.data)
            return
        elif message.command != 'PRIVMSG':
            return

        channel = message.params[0]
        sender = message.sender.removesuffix(suffix)

        if sender != bancho:
            await self.on_chat(channel, sender, message.data)
            return

        # BANCHO CHAT EVENTS

        elif match := re.match(r"(.+) joined in slot \d+.", message.data):
            name = match.group(1)
            await self.on_join(channel, name)
        elif match := re.match(r"(.+) left the game.", message.data):
            name = match.group(1)
            await self.on_leave(channel, name)
        elif match := re.match(r"(.+) became the host.", message.data):
            name = match.group(1)
            await self.on_host_new(channel, name)
        elif match := re.match(r"Beatmap changed to: (.+) \(https://osu.ppy.sh/b/(\d+)\)", message.data):
            beatmap_name = match.group(1)
            beatmap_id = match.group(2)
            await self.on_beatmap_change(channel, beatmap_name, beatmap_id)
        elif message.data == 'The match has started!':
            await self.on_match_start(channel)
        elif message.data == 'All players are ready':
            await self.on_ready(channel)
        # for now, let's treat aborting and clean finish as the same thing
        # this is subject to change
        elif message.data == 'The match has finished!' or message.data == 'Aborted the match':
            await self.on_match_end(channel)
        elif message.data == 'Host is changing map...':
            await self.on_host_choosing(channel)
        else:
            print(f"({channel}) {bancho}: {message.data}")
