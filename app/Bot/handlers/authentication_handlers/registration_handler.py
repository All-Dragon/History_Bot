import aiohttp
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.Bot.utils.keyboards import get_markup_registration_role
from app.core.config_app import Config, load_config

config: Config = load_config()

registration_router = Router()


class RegistrationState(StatesGroup):
    fill_username = State()
    fill_role = State()
    fill_password = State()


@registration_router.message(Command("registration"))
async def start_registration(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(telegram_id=message.from_user.id)
    await message.answer(
        "Введите ваше имя.\n"
        "Можно использовать только буквы и пробелы."
    )
    await state.set_state(RegistrationState.fill_username)


@registration_router.message(
    StateFilter(RegistrationState.fill_username),
    lambda x: x.text and all(part.isalpha() for part in x.text.split()),
)
async def get_username(message: Message, state: FSMContext) -> None:
    await state.update_data(username=message.text.strip())
    await message.answer(
        "Пожалуйста, укажите вашу роль:",
        reply_markup=get_markup_registration_role(),
    )
    await state.set_state(RegistrationState.fill_role)


@registration_router.message(StateFilter(RegistrationState.fill_username))
async def invalid_username(message: Message) -> None:
    await message.answer("Имя должно содержать только буквы и пробелы.")


@registration_router.callback_query(
    StateFilter(RegistrationState.fill_role),
    F.data.in_(["Ученик", "Преподаватель"]),
)
async def get_role(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(role=callback.data, is_banned=False)
    await callback.message.answer(
        "Теперь придумайте пароль для входа.\n"
        "Минимум 6 символов."
    )
    await state.set_state(RegistrationState.fill_password)


@registration_router.callback_query(StateFilter(RegistrationState.fill_role))
async def invalid_role(callback: CallbackQuery) -> None:
    await callback.answer(
        "Пожалуйста, выберите роль кнопкой.",
        show_alert=True,
    )


@registration_router.message(StateFilter(RegistrationState.fill_password), F.text)
async def get_password(message: Message, state: FSMContext) -> None:
    password = message.text.strip()

    if len(password) < 6:
        await message.answer("Пароль должен содержать минимум 6 символов.")
        return

    await state.update_data(password=password)
    data = await state.get_data()

    try:
        await message.delete()
    except Exception:
        pass

    await message.answer("Регистрирую вас в системе...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.api.base_url}/users/create",
                json=data,
            ) as response:
                if response.status < 300:
                    await message.answer(
                        "Вы успешно зарегистрированы!\n"
                        "Теперь войдите в систему командой /login."
                    )
                    await state.clear()
                    return

                if response.status == 400:
                    await message.answer(
                        "Вы уже зарегистрированы.\n"
                        "Попробуйте войти через /login."
                    )
                    await state.clear()
                    return

                error_text = await response.text()
                await message.answer(
                    f"Ошибка создания пользователя: {error_text or 'попробуйте позже'}"
                )

    except aiohttp.ClientConnectorError:
        await message.answer(
            "Ошибка подключения: API-сервер недоступен. "
            "Проверьте, запущен ли FastAPI."
        )
    except Exception:
        await message.answer(
            "Ошибка сервера, пожалуйста, попробуйте позже."
        )


@registration_router.message(StateFilter(RegistrationState.fill_password))
async def invalid_password(message: Message) -> None:
    await message.answer("Введите пароль обычным текстовым сообщением.")
