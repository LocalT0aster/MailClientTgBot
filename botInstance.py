import os

from dotenv import load_dotenv

from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot, StateMemoryStorage

load_dotenv('.env')

# Telegram info
TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN')
TELEGRAM_USER_ID = os.environ.get('USER_ID')

storage = StateMemoryStorage()
bot = AsyncTeleBot(TELEGRAM_TOKEN, state_storage=storage)
bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.IsDigitFilter())
