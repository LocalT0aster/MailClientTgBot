#!/usr/bin/python3
import asyncio
import logging
import os
import random
from sys import exit
from time import time

import telebot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage

from botInstance import bot, state_storage
from mailHandle import check_email

chats: list[int] = []
user_dict = {}

email_routine_handle = None

async def email_routine():
    while True:
        try:
            task = asyncio.create_task(check_email(chats))
            await asyncio.sleep(30)
            await task
        except asyncio.CancelledError:
            logging.error('email_routine Task Cancelled.')
            break
        except Exception as e:
            logging.error(e)


async def state_eq(message: telebot.types.Message, state: State):
    st = await state_storage.get_state(message.chat.id, message.from_user.id)
    return st == state


def load_chats():
    global chats
    try:
        if not os.path.exists("chats.txt"):
            with open('chats.txt', 'w') as f:
                f.flush()
                f.close()
            return
        chats = [int(u) for u in open('chats.txt', 'r').readlines()]
    except OSError as e:
        logging.error(e)


def write_chats(chats: list[int] = chats):
    try:
        with open('chats.txt', 'w') as f:
            f.write('\n'.join(str(u) for u in chats) + '\n')
            f.flush()
            f.close()
    except OSError as e:
        logging.error(e)


@bot.message_handler(commands='cancel')
async def any_state(message: telebot.types.Message):
    await bot.send_message(message.chat.id, "Your state was cancelled.")
    await bot.delete_state(message.from_user.id, message.chat.id)

class RegisterStep(StatesGroup):
    code = State()

@bot.message_handler(commands=['help'])
async def help(message: telebot.types.Message):
    await bot.send_message(message.chat.id, '/help\n/start\n/stop\n/cancel')

@bot.message_handler(commands=['start', 'register'])
async def start(message: telebot.types.Message):
    global chats
    if message.chat.id not in chats:
        code = random.randint(100000, 999999)
        print(f'Code for {message.chat.id} is {code}')
        await bot.send_message(577772675, f'Code for @{message.from_user.username} is\n```txt\n{code}\n```', parse_mode='MarkdownV2')
        user_dict[message.chat.id] = code
        await bot.send_message(message.chat.id, 'Send the generated password.')
        await bot.set_state(message.from_user.id, RegisterStep.code, message.chat.id)
        return
    await bot.reply_to(message, 'You are already registered!')

@bot.message_handler(func= lambda msg: state_eq(msg, RegisterStep.code), content_types=['text'])
async def register2(message: telebot.types.Message):
    code = user_dict[message.chat.id]
    user_dict.pop(message.chat.id)
    if int(message.text) != code:
        await bot.send_message(message.chat.id, 'Wrong code, try again.')
        logging.warning(f'User {message.from_user.username} sent wrong code')
        return
    global chats
    chats.append(message.chat.id)
    write_chats(chats)
    logging.warning(f'User {message.from_user.username} added to mailing llist')
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.send_message(message.chat.id, 'Added to the mailing list successfully.')


@bot.message_handler(commands='stop')
async def stop(message: telebot.types.Message):
    global email_routine_handle
    email_routine_handle.cancel()
    exit(0)


async def main():
    random.seed(time())
    load_chats()
    logging.warning('Bot is running')
    polling = asyncio.create_task(bot.infinity_polling())
    global email_routine
    email_routine = asyncio.create_task(email_routine())
    await email_routine
    await polling


if __name__ == '__main__':
    asyncio.run(main())
