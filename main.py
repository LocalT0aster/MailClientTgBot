import email
import imaplib

import telegram
from telegram.ext import CommandHandler, Updater

# Telegram Bot Token
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
# Your Telegram User ID
TELEGRAM_USER_ID = YOUR_TELEGRAM_USER_ID

# Email Server Information
SMTP_SERVER = "YOUR_SMTP_SERVER"
SMTP_PORT = 993  # Usually 993 for SSL
EMAIL_ACCOUNT = "YOUR_EMAIL"
EMAIL_PASSWORD = "YOUR_PASSWORD"

# Connect to Telegram
bot = telegram.Bot(token=TELEGRAM_TOKEN)
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)

def check_email(update, context):
    mail = imaplib.IMAP4_SSL(SMTP_SERVER, SMTP_PORT)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select('inbox')

    result, data = mail.search(None, 'UNSEEN')
    mail_ids = data[0]

    id_list = mail_ids.split()
    for i in id_list:
        result, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                email_subject = msg['subject']
                email_from = msg['from']
                bot.send_message(chat_id=TELEGRAM_USER_ID, text=f"New Email\nFrom: {email_from}\nSubject: {email_subject}")

def start(update, context):
    update.message.reply_text('Email monitoring started!')
    check_email(update, context)

start_handler = CommandHandler('start', start)
updater.dispatcher.add_handler(start_handler)
updater.start_polling()
updater.idle()
