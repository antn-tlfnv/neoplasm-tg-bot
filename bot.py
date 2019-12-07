"""
Neoplasm Telegram Bot
"""

import logging
import os
from pprint import pprint

import aiohttp
import pymongo
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiohttp import web
from pymongo import MongoClient

TOKEN = os.environ.get('TG_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

routes = web.RouteTableDef()


@dp.message_handler(commands='start')
async def start(message: types.Message):
    await message.reply(
        'Welcome to Neoplasm Bot\nTo register an item use /register'
    )


@dp.message_handler(commands='help')
async def help(message: types.Message):
    await message.reply(
        'This is Neoplasm Bot\nTo register an item use /register'
    )


class Registration(StatesGroup):
    otp = State()


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    await state.finish()
    await message.reply('Cancelled', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands='register')
async def register(message: types.Message):
    await message.reply(
        'Send me the code'
    )

    await Registration.otp.set()


@dp.message_handler(
    lambda message: not message.text.isdigit(),
    state=Registration.otp
)
async def register_(message: types.Message):
    return await message.reply('Not integer\nCode must be 6 digits number\nEnter valid code or use /cancel to quit')


@dp.message_handler(
    lambda message: message.text.isdigit() and len(message.text) != 6,
    state=Registration.otp
)
async def process_age_invalid(message: types.Message):
    return await message.reply('Not 6 digits\nCode must be 6 digits number\nEnter valid code or use /cancel to quit')


@dp.message_handler(
    lambda message: message.text.isdigit() and len(message.text) == 6,
    state=Registration.otp
)
async def process_name(message: types.Message, state: FSMContext):
    otp = message.text

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://neoplasm-api.herokuapp.com/itemVerify?otp={otp}&tg_user_id={message.from_user.id}') as resp:
            response = await resp.json()
            registered = response['registered']
            print(response)
            if registered:
                await message.reply(f'You are registered\nWelcome to Neoplasm!')
                await state.finish()

            else:
                await message.reply(f'Wrong code\nTry another or use /cancel to quit')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
