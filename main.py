import os
import asyncio
import typing
from connector import IrcHandler

# load settings from environment variables
host = os.getenv('IRC_HOST')
port = int(os.getenv('IRC_PORT'))
username = os.getenv('IRC_USERNAME')
password = os.getenv('IRC_PASSWORD')
running = True

# receive messages from irc connection and send off to process in other functions
async def main():
    async with IrcHandler(host, port) as client:
        await client.login(username, password)
        await client.privmsg('BanchoBot', '!mp help')
        while True:
            msg = await client.recv_msg()
            if msg.command == 'PRIVMSG':
                print(msg)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Killed")
