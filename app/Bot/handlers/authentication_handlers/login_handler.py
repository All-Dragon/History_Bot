import aiohttp
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.Bot.utils.keyboards import get_change_username_markup
from app.core.config_app import Config, load_config

config: Config = load_config()


class LoginStates(StatesGroup):
    waiting_password = State()


class ChangeNameState(StatesGroup):
    waiting_name = State()


login_router = Router()


@login_router.message(Command("login"))
async def login(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    await state.clear()
    await state.update_data(login_telegram_id=telegram_id)
    await message.answer(
        f"Ваш Telegram ID: <b>{telegram_id}</b>\n\n"
        "Введите ваш пароль для входа в систему.",
        parse_mode="HTML",
    )
    await state.set_state(LoginStates.waiting_password)


@login_router.message(StateFilter(LoginStates.waiting_password), F.text)
async def confirm_login(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    password = message.text.strip()

    if not password:
        await message.answer("Пароль не может быть пустым. Попробуйте еще раз.")
        return

    try:
        await message.delete()
    except Exception:
        pass

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.api.base_url}/auth/login",
                json={"telegram_id": telegram_id, "password": password},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    await message.answer(
                        f"Ошибка авторизации: {error_text or 'сервер не отвечает'}"
                    )
                    await state.clear()
                    return

                token_data = await response.json()
                access_token = token_data["access_token"]

                await state.update_data(user_token=access_token)
                await state.set_state(None)

                await message.answer(
                    "Успешная авторизация!\n"
                    "Теперь вы можете пользоваться командами бота."
                )
    except aiohttp.ClientConnectorError:
        await message.answer(
            "Ошибка подключения: API-сервер недоступен. "
            "Проверьте, запущен ли FastAPI."
        )
        await state.clear()
    except Exception:
        await message.answer(
            "Ошибка сервера, пожалуйста, попробуйте позже."
        )
        await state.clear()


@login_router.message(Command("profile"))
async def get_my_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    token = data.get("user_token")

    if not token:
        await message.answer("Сначала войдите в систему командой /login")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.api.base_url}/users/me",
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                if response.status == 401:
                    await message.answer(
                        "Сессия истекла. Пожалуйста, войдите заново: /login"
                    )
                    await state.clear()
                    return

                if response.status != 200:
                    await message.answer(
                        "Ошибка сервера, попробуйте позже."
                    )
                    return

                response_data = await response.json()
                ban_status = (
                    "Не забанен" if response_data.get("is_banned") is False else "Бан"
                )
                text = (
                    f"Ваш никнейм: {response_data.get('username', 'Не указан')}\n"
                    f"Ваша роль: {response_data.get('role', 'Нет роли')}\n"
                    f"Статус бана: {ban_status}"
                )
                await message.answer(text)
    except Exception:
        await message.answer(
            "Ошибка сервера, пожалуйста, попробуйте позже."
        )


@login_router.message(Command("change_name"))
async def change_username(message: Message, state: FSMContext):
    await message.answer(
        "Вы хотите сменить ваше имя пользователя?",
        reply_markup=get_change_username_markup(),
    )


@login_router.callback_query(F.data == "change_name_yes")
async def fill_get_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeNameState.waiting_name)
    await callback.answer()
    await callback.message.edit_text(
        "Пожалуйста, напишите новое имя пользователя:"
    )
    await state.update_data(message_id=callback.message.message_id)


@login_router.message(StateFilter(ChangeNameState.waiting_name), F.text)
async def fill_change_name(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    new_name = message.text.strip()
    data = await state.get_data()
    token = data.get("user_token")

    if not token:
        await message.answer("Сначала войдите в систему командой /login")
        await state.clear()
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{config.api.base_url}/users/me/name",
                json={"name": new_name},
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                if response.status == 401:
                    await message.answer(
                        "Сессия истекла. Пожалуйста, войдите заново: /login"
                    )
                    await state.clear()
                    return

                if response.status != 200:
                    await message.answer(
                        "Ошибка сервера, попробуйте позже."
                    )
                    return

                response_data = await response.json()
                ban_status = (
                    "Не забанен" if response_data.get("is_banned") is False else "Бан"
                )
                text = (
                    "Смена имени пользователя прошла успешно!\n\n"
                    f"Ваш никнейм: {response_data.get('username', 'Не указан')}\n"
                    f"Ваша роль: {response_data.get('role', 'Нет роли')}\n"
                    f"Статус бана: {ban_status}"
                )

                await message.bot.edit_message_text(
                    message_id=data.get("message_id"),
                    chat_id=message.chat.id,
                    text=text,
                )
                await state.set_state(None)
    except Exception:
        await message.answer(
            "Ошибка сервера, пожалуйста, попробуйте позже."
        )


@login_router.callback_query(F.data == "change_name_no")
async def cancel_change_name(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        "Отмена смены имени",
        reply_markup=None,
    )
