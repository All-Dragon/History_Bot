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
from Bot.utils.auth_check import check_user_has_role
import aiohttp
from typing import Callable, Awaitable, Any
from Bot.utils.keyboards import get_markup_registration_role
import asyncio

config: Config = load_config()

stats_router = Router()

@stats_router.message(Command('users_states'))
async def get_all_users_states(message: Message, state: FSMContext):
    if not await check_user_has_role(message, state, ['Админ']):
        return
    data = await state.get_data()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{
                config.api.base_url}/stats/admin/overview',
                headers={"Authorization": f"Bearer {data['user_token']}"}
            ) as resp:

                if resp.status == 401:
                    await message.answer("Сессия истекла. Пожалуйста, войдите заново: /login")
                    await state.clear()
                    return

                if resp.status != 200:
                    await message.answer('Ошибка сервера, попробуйте позже!')
                    return

                data = await resp.json()

                text = (f"Статистика по использованию бота:\n\n"
                        f"Всего пользователей: {data.get('total_user', 'Нет данных')}\n"
                        f"Активных пользователей: {data.get('current_user', 'Нет данных')}\n"
                        f"Пользователей удаливших аккаунт: {data.get('deleted_user', 'Нет данных')}")

                await state.clear()
                await message.answer(text)

    except Exception as e:
        error_msg = ('Ошибка сервера, пожалуйста, попробуйте позже')

        await state.clear()
        await message.answer(error_msg)


@stats_router.message(Command('my_stats'))
async def get_my_states(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'{config.api.base_url}/stats/my_stats',
                    headers={"Authorization": f"Bearer {data['user_token']}"}
            ) as resp:

                if resp.status == 401:
                    await message.answer("Сессия истекла. Пожалуйста, войдите заново: /login")
                    await state.clear()
                    return

                if resp.status != 200:
                    await message.answer('Ошибка сервера, попробуйте позже!')
                    return

                data = await resp.json()

                text = (f"Статистика по ответам на вопросы:\n\n"
                        f"Всего вопросов решено: {data.get('total_question', 'Нет данных')}\n"
                        f"Правильных ответов дано: {data.get('right_answer', 'Нет данных')}\n"
                        f"Доля правильных ответов: {data.get('right_answer_percentage', 'Нет данных')}")

                await state.clear()
                await message.answer(text)

    except Exception as e:
        error_msg = ('Ошибка сервера, пожалуйста, попробуйте позже')

        await state.clear()
        await message.answer(error_msg)