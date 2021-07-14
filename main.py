import os
import asyncio
import typing
from connector import IrcHandler
from lobby import LobbyManager

# load settings from environment variables
host = os.getenv('IRC_HOST')
port = int(os.getenv('IRC_PORT'))
username = os.getenv('IRC_USERNAME')
password = os.getenv('IRC_PASSWORD')
lobbyname = os.getenv('LOBBY_NAME')

# receive messages from irc connection and send off to process in other functions
async def main():
    async with IrcHandler(host, port) as client:
        await client.login(username, password)
        async with LobbyManager(client, username, lobbyname) as manager:
            print(f"Joined channel {manager.channel}")
            while True:
                await manager.process_msg()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
