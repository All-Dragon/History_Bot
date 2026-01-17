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

class RegistrationBlockMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):

        # Пропускаем всё, кроме сообщений
        if not isinstance(event, Message):
            return await handler(event, data)

        # Пропускаем всё, кроме /registration
        if not event.text:
            return await handler(event, data)

        command = event.text.split()[0]
        if not command.startswith('/registration'):
            return await handler(event, data)

        telegram_id = event.from_user.id

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{config.api.base_url}/users/{telegram_id}'
                ) as response:

                    if response.status == 200:
                        await event.answer('⚠️ Вы уже зарегистрированы!')
                        return  # ❌ дальше не идём

                    if response.status == 404:
                        return await handler(event, data)  # ✅ можно регаться

                    # ВСЕ остальные статусы
                    await event.answer(
                        '⚠️ Не удалось проверить регистрацию, попробуйте позже'
                    )
                    return

        except aiohttp.ClientConnectorError:
            await event.answer('⚠️ Сервер недоступен')
            return

        except Exception as e:
            await event.answer(f'❌ Ошибка: {str(e)[:100]}')
            return



registration_router = Router()
registration_router.message.middleware(RegistrationBlockMiddleware())

class RegistrationState(StatesGroup):
    fill_username = State()
    fill_role = State()

@registration_router.message(Command('registration'))
async def start_registration(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(telegram_id = message.from_user.id)
    await message.answer('Пожалуйста, введите ваше имя')
    await state.set_state(RegistrationState.fill_username)



@registration_router.message(StateFilter(RegistrationState.fill_username), lambda x: x.text and all([i.isalpha() for i in x.text.split()]))
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

@registration_router.message(StateFilter(RegistrationState.fill_username))
async def invalid_username(message: Message) -> None:
    await message.answer(
        "Имя должно содержать только буквы и пробелы"
    )

@registration_router.callback_query(StateFilter(RegistrationState.fill_role), F.data.in_(['Ученик', 'Преподаватель']))
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

                elif response.status == 409:
                    await callback.message.answer(
                        '⚠️ Вы уже зарегистрированы в системе'
                    )
                    await state.clear()

                else:
                    await callback.message.answer('Ошибка создания')


    except aiohttp.ClientConnectorError:
        await callback.message.answer(
            "⚠️ Ошибка подключения: Сервер API недоступен. Проверьте, запущен ли FastAPI."
        )
    except Exception as e:
        await callback.message.answer(f"❌ Произошла непредвиденная ошибка: {str(e)[:100]}")



@registration_router.callback_query(StateFilter(RegistrationState.fill_role))
async def invalid_role(callback: CallbackQuery) -> None:
    await callback.answer("Пожалуйста, выберите вариант кнопкой", show_alert=True)

