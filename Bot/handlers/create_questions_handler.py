from aiogram import Dispatcher, Bot, types, F, BaseMiddleware, Router
from aiogram.filters import CommandStart, Command, BaseFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardMarkup,InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, ReplyKeyboardRemove,
                           KeyboardButtonPollType, BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, TelegramObject, User, InputMediaAudio,
                           InputMediaDocument, InputMediaPhoto,
                           InputMediaVideo, PhotoSize)
from config_app import Config, load_config
import aiohttp
from typing import Callable, Awaitable, Any
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
import asyncio

config: Config = load_config()
questions_router = Router()

class QuestionState(StatesGroup):
    question_type = State()
    text = State()
    topic = State()
    difficulty = State()
    options = State() # Только для multiple_choice
    correct_answer = State()
    status = State()
    image = State() # Если будет фотка, необязательное поле
    preview = State()


@questions_router.message(Command('add_questions'))
async def add_question(message: Message, state: FSMContext):
    data = await state.get_data()
    user_token = data.get('user_token')

    if not user_token:
        await message.answer("Сначала войдите в систему командой /login")
        return



