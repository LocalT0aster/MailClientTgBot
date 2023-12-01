import os

from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot

load_dotenv('.env')

# Telegram info
TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN')
TELEGRAM_USER_ID = os.environ.get('USER_ID')

bot = AsyncTeleBot(TELEGRAM_TOKEN, 'MarkdownV2')
