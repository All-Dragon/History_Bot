from dotenv import load_dotenv
import logging
import os
from aiogram import Dispatcher, Bot, types, F, BaseMiddleware
from aiogram.filters import CommandStart, Command, BaseFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardMarkup,InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, ReplyKeyboardRemove,
                           KeyboardButtonPollType, BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, TelegramObject, User, InputMediaAudio,
                           InputMediaDocument, InputMediaPhoto,
                           InputMediaVideo, PhotoSize)
from aiogram.enums import PollType
import asyncio
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup, KeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import create_engine, String, Integer, ForeignKey, text, Boolean, select, or_, desc, asc, func, Table, \
    Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship, selectinload, joinedload, \
    sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from pydantic import BaseModel, Field
import random
from aiogram.exceptions import  TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
import datetime
import re
from aiogram import Router
from aiogram.client.bot import Bot
from aiogram.filters.callback_data import CallbackData
from typing import Any, Awaitable, Callable
import aiohttp
from config_app import Config, load_config
from Bot.lexicon import lexicon
config: Config = load_config()

bot_token = config.bot.token
admin_ids = config.bot.admin_ids

storage = MemoryStorage()

bot = Bot(token = bot_token)

dp = Dispatcher(storage = storage)

class RegistrationState(StatesGroup):
    fill_username = State()
    fill_role = State()


@dp.message(CommandStart())
async def start_bot(message: Message) -> None:
    await message.answer(f'Привет, {message.from_user.username}!. Добро пожаловать в History Bot! \nДля получения помощи используй команду /help')

@dp.message(Command('help'))
async def help(message: Message) -> None:
    await message.answer(lexicon['/help'])

@dp.message(Command('registration'))
async def start_registration(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(telegram_id = message.from_user.id)
    await message.answer('Пожалуйста, введите ваше имя')
    await state.set_state(RegistrationState.fill_username)



@dp.message(StateFilter(RegistrationState.fill_username), lambda x: x.text and all([i.isalpha() for i in x.text.split()]))
async def get_username(message: Message, state: FSMContext) -> None:
    await state.update_data(username = message.text)

    kb_builder = InlineKeyboardBuilder()
    button1 = InlineKeyboardButton(text = 'Ученик', callback_data= 'Ученик')
    button2 = InlineKeyboardButton(text = 'Преподаватель', callback_data= 'Преподаватель')

    kb_builder.add(button1, button2)
    kb_builder.adjust(1, 1)
    markup = kb_builder.as_markup()

    await message.answer('Пожалуйста, укажите кто Вы', reply_markup= markup)
    await state.set_state(RegistrationState.fill_role)

@dp.message(StateFilter(RegistrationState.fill_username))
async def invalid_username(message: Message) -> None:
    await message.answer(
        "Имя должно содержать только буквы и пробелы"
    )

@dp.callback_query(StateFilter(RegistrationState.fill_role), F.data.in_(['Ученик', 'Преподаватель']))
async def get_role(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    role = callback.data
    await state.update_data(role = role)
    await state.update_data(is_banned = False)

    await callback.message.answer('Загружаем данные')
    data = await state.get_data()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{config.api.base_url}/users/create', json= data) as response:
                if response.status < 300:
                    await callback.message.answer('Вы зарегистрировались!')
                    await state.clear()
                else:
                    await callback.message.answer('Ошибка создания')


    except aiohttp.ClientConnectorError:
        await callback.message.answer(
            "⚠️ Ошибка подключения: Сервер API недоступен. Проверьте, запущен ли FastAPI."
        )
    except Exception as e:
        await callback.message.answer(f"❌ Произошла непредвиденная ошибка: {str(e)[:100]}")



@dp.callback_query(StateFilter(RegistrationState.fill_role))
async def invalid_role(callback: CallbackQuery) -> None:
    await callback.answer("Пожалуйста, выберите вариант кнопкой", show_alert=True)



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())