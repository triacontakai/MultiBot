import os
import asyncio
import typing
import test

# load settings from environment variables
host = os.getenv('IRC_HOST')
port = int(os.getenv('IRC_PORT'))
username = os.getenv('IRC_USERNAME')
password = os.getenv('IRC_PASSWORD')
lobbyname = os.getenv('LOBBY_NAME')

client = test.TestClient(host, port)
client.run(username, password)
