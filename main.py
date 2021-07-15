import os
import asyncio
import typing
import irc

# load settings from environment variables
host = os.getenv('IRC_HOST')
port = int(os.getenv('IRC_PORT'))
username = os.getenv('IRC_USERNAME')
password = os.getenv('IRC_PASSWORD')
lobbyname = os.getenv('LOBBY_NAME')

client = irc.Client(host, port)

@client.event
async def on_init(client):
    print(f"logged in as {client.username} on {client.host}:{client.port}")

@client.event
async def on_message(client, message):
    if message.command != 'QUIT':
        print(message)

client.run(username, password)
