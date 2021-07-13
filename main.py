import os

# load settings from environment variables
host = os.getenv('IRC_HOST')
port = int(os.getenv('IRC_PORT'))
username = os.getenv('IRC_USERNAME')
password = os.getenv('IRC_PASSWORD')
