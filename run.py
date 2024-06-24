#!/usr/bin/python3
import asyncio
import logging
import os
import random
from sys import exit
from time import time

from botInstance import bot, storage
from mailHandle import check_email
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.types import Message

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARN
)

YOUR_USER_ID = int(os.environ.get("USER_ID"))

COMMANDS = ('/start or /register\n'
            '/help\n'
            '/subscribe\n'
            '/unsubscribe\n'
            '/unregister\n'
            '/cancel\n'
            '/stop\n')

chats: list[int] = []
subs: list[int] = []

email_routine_handle = None


async def email_routine():
    while True:
        try:
            task = asyncio.create_task(check_email(subs))
            await asyncio.sleep(60)
            await task
        except asyncio.CancelledError:
            logging.error('email_routine Task Cancelled.')
            break
        except Exception as e:
            logging.error(e)


def load_db():
    global chats, subs
    try:
        if os.path.exists("chats.txt"):
            chats = [int(u) for u in filter(lambda l: l.isdigit(), open('chats.txt', 'r').readlines())]
        if os.path.exists("subs.txt"):
            subs = [int(s) for s in filter(lambda l: l.isdigit(), open('subs.txt', 'r').readlines())]
    except OSError as e:
        logging.error(e)


def write_db():
    global chats, subs
    try:
        with open('chats.txt', 'w') as f:
            f.write('\n'.join(str(u) for u in chats) + '\n')
            f.flush()
            f.close()
        with open('subs.txt', 'w') as f:
            f.write('\n'.join(str(s) for s in subs) + '\n')
            f.flush()
            f.close()
    except OSError as e:
        logging.error(e)


@bot.message_handler(commands='cancel', state='*')
async def cancel_state(message: Message):
    await bot.reply_to(message, "Your state was cancelled.")
    await bot.delete_state(message.from_user.id, message.chat.id)


class RegisterStep(StatesGroup):
    code = State()


@bot.message_handler(commands=['help'], state=None)
async def help(message: Message):
    await bot.send_message(message.chat.id, COMMANDS)


@bot.message_handler(commands=['start', 'register'], state=None)
async def start(message: Message):
    global chats
    if message.chat.id not in chats:
        code = random.randint(100000, 999999)
        print(f'Code for {message.chat.id} is {code}')
        msgs: list[int] = []
        # Save code
        await storage.set_data(message.chat.id, message.from_user.id, 'code', code)
        # Send code to YOUR_USER_ID & save the message id
        await storage.set_data(message.chat.id, message.from_user.id, 'codemsg',
                               (await bot.send_message(YOUR_USER_ID, 'Code for @{} is\n```txt\n{}\n```'
                                                       .format(message.from_user.username.replace('_', '\\_'), code),
                                                       parse_mode='MarkdownV2')).id)
        # Save the request to send code message.id
        await storage.set_data(message.chat.id, message.from_user.id, 'msgids',
                               [(await bot.reply_to(message, 'Send the generated password.')).id])
        # Set user state to RegisterStep.code
        await storage.set_state(message.from_user.id, message.chat.id, RegisterStep.code)
        return
    await bot.reply_to(message, 'You are already registered!')


@bot.message_handler(state=RegisterStep.code)
async def register_code(message: Message):
    chat_id, user_id, username = message.chat.id, message.from_user.id, message.from_user.username
    code: int = (await storage.get_data(chat_id, user_id))['code']
    codemsg: int = (await storage.get_data(message.chat.id, message.from_user.id))['codemsg']
    msgs: list[int] = (await storage.get_data(chat_id, user_id))['msgids']
    msgs.append(message.id)
    if not code and (message.text != str(code)):
        await storage.delete_state(user_id, chat_id)
        await bot.send_message(chat_id, 'Wrong code, try again.')
        logging.warning(f'User @{username} sent the wrong code')

        await bot.delete_message(YOUR_USER_ID, codemsg, 10)
        for msg in msgs:
            await bot.delete_message(chat_id, msg, 10)
        await storage.reset_data(chat_id, user_id)
        return
    global chats
    chats.append(chat_id)
    write_db()
    logging.warning(f'User @{username} has registered.')
    await bot.send_message(YOUR_USER_ID, f'User @{username} has registered.')

    await bot.delete_message(YOUR_USER_ID, codemsg, 10)
    for msg in msgs:
        await bot.delete_message(chat_id, msg, 10)

    await storage.reset_data(chat_id, user_id)
    await storage.delete_state(user_id, chat_id)
    await bot.send_message(chat_id, 'Registered successfully.')


@bot.message_handler(commands='subscribe', state=None)
async def subscribe(message: Message):
    global chats, subs
    if (message.chat.id not in chats):
        await bot.reply_to(message, 'You are not registered!\nType /register to register')
        return
    subs.append(message.chat.id)
    write_db()
    await bot.reply_to(message, 'Successfully added you to the mailing list.')


@bot.message_handler(commands='unsubscribe', state=None)
async def unsubscribe(message: Message):
    global chats, subs
    if (message.chat.id not in chats):
        await bot.reply_to(message, 'You are not registered!\nType /register to register')
        return
    if (message.chat.id not in subs):
        await bot.reply_to(message, 'You were not subscribed.')
        return
    subs.remove(message.chat.id)
    write_db()
    await bot.reply_to(message, 'Successfully removed you from the mailing list.')


@bot.message_handler(commands='unregister', state=None)
async def unregister(message: Message):
    global chats, subs
    if (message.chat.id in subs):
        subs.remove(message.chat.id)
    if (message.chat.id not in chats):
        await bot.reply_to(message, 'You were not registered.')
        return
    chats.remove(message.chat.id)
    write_db()
    await bot.reply_to(message, 'Successfully removed you from the database.')


@bot.message_handler(commands='stop', state='*')
async def stop(message: Message):
    if (message.chat.id not in chats):
        await bot.reply_to(message, 'You are not registered!\nType /register to register')
        return
    global email_routine_handle
    email_routine_handle.cancel()
    bot.reply_to(message, 'Exiting...')
    exit(0)


async def main():
    random.seed(time())
    load_db()
    logging.warning('Bot is running')
    polling = asyncio.create_task(bot.infinity_polling())
    global email_routine_handle
    email_routine_handle = asyncio.create_task(email_routine())
    await email_routine_handle
    await polling


if __name__ == '__main__':
    asyncio.run(main())
