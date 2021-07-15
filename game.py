import asyncio
import typing
from irc.py import IRCSocket

class GameManager:
    host: str
    port: int
    username: str
    client: IRCSocket

    def __init__(self, host, port):
        
