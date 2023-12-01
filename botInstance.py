import os

from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot, StateMemoryStorage

load_dotenv('.env')

# Telegram info
TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN')
TELEGRAM_USER_ID = os.environ.get('USER_ID')

state_storage = StateMemoryStorage()
bot = AsyncTeleBot(TELEGRAM_TOKEN, state_storage=state_storage)
