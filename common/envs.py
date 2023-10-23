import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
RPC_ENDPOINT = os.getenv('RPC_ENDPOINT')
RPC_PORT = os.getenv('RPC_PORT')
RPC_USER = os.getenv('RPC_USER')
RPC_PASSWORD = os.getenv('RPC_PASSWORD')
WALLET_PASSWORD = os.getenv('WALLET_PASSWORD')
USER_ID = int(os.getenv('USER_ID'))
API = os.getenv('API')
DATA_PATH = os.getenv('DATA_PATH')
RPC_URL = f'http://{RPC_USER}:{RPC_PASSWORD}@{RPC_ENDPOINT}:{RPC_PORT}/'
