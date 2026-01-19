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

class LoginStates(StatesGroup):
    waiting_confirm = State()

def kb_builder() -> InlineKeyboardBuilder:
    kb_builder = InlineKeyboardBuilder()
    bt1 = InlineKeyboardButton(text = 'Да', callback_data= 'yes')
    bt2 = InlineKeyboardButton(text = 'Нет', callback_data = 'no')
    markup = kb_builder.add(bt1, bt2).adjust(1, 1).as_markup()
    return markup

login_router = Router()


@login_router.message(Command('login'))
async def login(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    await message.answer(f"Ваш Telegram ID: <b>{telegram_id}</b>\n\n"
        "Это ваш идентификатор в системе. Подтвердите, чтобы получить доступ к функциям.",
                   reply_markup= kb_builder(),
                   parse_mode= 'HTML')

    await state.set_state(LoginStates.waiting_confirm)

@login_router.callback_query(StateFilter(LoginStates.waiting_confirm), F.data == 'yes')
async def confirm_login(callback: CallbackQuery, state = FSMContext):
    await callback.answer()
    telegram_id = callback.from_user.id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{config.api.base_url}/auth/login', json= {'telegram_id': telegram_id}) as response:

                if response.status != 200:
                    error_text = await response.text()
                    await callback.message.edit_text(
                        f"Ошибка авторизации: {error_text or 'Сервер не отвечает'}"
                    )
                    await state.clear()
                    return

                token_data = await response.json()
                access_token = token_data['access_token']

                await state.update_data(user_token=access_token)

                await callback.message.edit_text(
                "✅ Успешная авторизация!\n"
                "Теперь вы можете использовать команды для учителей (/add_questions и т.д.)"
                )
    except Exception as e:
        await callback.message.answer(f'{str(e)}')

        await state.clear()


@login_router.callback_query(StateFilter(LoginStates.waiting_confirm), F.data == 'no')
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Авторизация отменена. Если ID неверный — проверьте настройки Telegram.")
    await state.clear()