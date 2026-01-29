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
from Bot.utils.keyboards import get_login_markup, get_change_username_markup
import asyncio

config: Config = load_config()

class LoginStates(StatesGroup):
    waiting_confirm = State()

class ChangeNameState(StatesGroup):
    waiting_name = State()


login_router = Router()


@login_router.message(Command('login'))
async def login(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    await message.answer(f"Ваш Telegram ID: <b>{telegram_id}</b>\n\n"
        "Это ваш идентификатор в системе. Подтвердите, чтобы получить доступ к функциям.",
                   reply_markup= get_login_markup(),
                   parse_mode= 'HTML')

    await state.set_state(LoginStates.waiting_confirm)

@login_router.callback_query(StateFilter(LoginStates.waiting_confirm), F.data == 'login_yes')
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
                "Теперь вы можете использовать команды для учителей (/add_question и т.д.)"
                )
    except Exception as e:
        await callback.message.answer('Ошибка сервера, пожалуйста, попробуйте позже')

        await state.clear()


@login_router.callback_query(StateFilter(LoginStates.waiting_confirm), F.data == 'login_no')
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Авторизация отменена. Если ID неверный — проверьте настройки Telegram.")
    await state.clear()


@login_router.message(Command('profile'))
async def get_my_profile(message: Message,
                         state: FSMContext):

    data = await state.get_data()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{config.api.base_url}/users/me',
                headers={'Authorization': f'Bearer {data.get('user_token')}'}
                    ) as response:

                if response.status == 401:
                    await message.answer("Сессия истекла. Пожалуйста, войдите заново: /login")
                    await state.clear()
                    return

                if response.status != 200:
                    await message.answer('Ошибка сервера, попробуйте позже!')
                    return

                response_text = await response.json()

                text = (f'Ваш никнейм: {response_text.get('username', 'Не указан')}\n'
                        f'Ваша роль: {response_text.get('role', 'Нет роли')}\n'
                        f'Статус бана: {"Не забанен" if response_text.get('is_banned') == False else "Бан"}')

                await message.answer(text)

    except Exception as e:
        print("Ошибка сервера, пожалуйста, попробуйте позже")


@login_router.message(Command('change_name'))
async def change_username(message: Message,
                          state: FSMContext):
    await message.answer('Вы хотите сменить ваше имя пользователя?', reply_markup = get_change_username_markup())

@login_router.callback_query(F.data == 'change_name_yes')
async def fill_get_name(callback: CallbackQuery,
                           state: FSMContext):
    await state.set_state(ChangeNameState.waiting_name)
    await callback.answer()
    await callback.message.edit_text('Пожалуйста, напишите новое имя пользователя:')
    await state.update_data(message_id = callback.message.message_id)

@login_router.message(StateFilter(ChangeNameState.waiting_name), F.text)
async def fill_change_name(message: Message,
                           state: FSMContext):
    await message.delete()
    new_name = message.text.strip()
    data = await state.get_data()
    token = data.get('user_token')

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f'{config.api.base_url}/users/me/name',
                json = {'name': new_name},
                headers={'Authorization': f"Bearer {data.get('user_token')}"}
            ) as response:

                if response.status == 401:
                    await message.answer("Сессия истекла. Пожалуйста, войдите заново: /login")
                    await state.clear()
                    return

                if response.status != 200:
                    await message.answer('Ошибка сервера, попробуйте позже!')
                    return

                response_text = await response.json()

                text = ('Смена имени пользователя прошла успешно!\n\n'
                        f'Ваш никнейм: {response_text.get('username', 'Не указан')}\n'
                        f'Ваша роль: {response_text.get('role', 'Нет роли')}\n'
                        f'Статус бана: {"Не забанен" if response_text.get('is_banned') == False else "Бан"}')

                await message.bot.edit_message_text(
                    message_id = data.get('message_id'),
                    chat_id= message.chat.id,
                    text = text
                )

    except Exception as e:
        await message.answer('Ошибка сервера, пожалуйста, попробуйте позже')

@login_router.callback_query(F.data == 'change_name_no')
async def cancel_change_name(callback: CallbackQuery,
                             state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text('Отмена смены имени', reply_markup= None)


