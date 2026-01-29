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
import asyncio
from Bot.utils.auth_check import check_user_has_role
from Bot.utils.keyboards import (
    get_markup_difficulty, get_markup_question_type, get_markup_status, get_markup_photo,
    get_progress_text, get_step_emoji, get_markup_navigation, get_markup_cancel_confirm,
    get_markup_back_cancel, get_markup_back_cancel_difficulty
)
from API.routers.questions_router.questions_shemas import MultipleChoiceCreate, FreeTextCreate

config: Config = load_config()
teacher_func_router = Router()

class ResultsStates(StatesGroup):
    waiting_results = State()

@teacher_func_router.message(Command('result'))
async def get_result_question_by_id(message: Message, state: FSMContext):
    args = message.text.split()[1:]

    data = await state.get_data()
    token = data.get('user_token')

    if not token:
        await message.answer("Вы не авторизованы. Войдите: /login")
        return

    if not args or not args[0].isdigit():
        await message.answer("Использование: /result <id вопроса>")
        return

    question_id = int(args[0])

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{config.api.base_url}/stats/questions/{question_id}/answers',
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                # Обработка статусов
                if response.status == 401:
                    await message.answer("Сессия истекла. Войдите заново: /login")
                    await state.clear()
                    return

                if response.status == 403:
                    await message.answer("Нет доступа к этому вопросу (возможно, вы не автор)")
                    return

                if response.status == 404:
                    await message.answer(f"Вопрос #{question_id} не найден")
                    return

                if response.status != 200:
                    error_text = await response.text()
                    await message.answer(f"Ошибка сервера: {response.status} — {error_text}")
                    return

                result = await response.json()

                if not result:
                    await message.answer(f"По вопросу #{question_id} пока никто не ответил.")
                    return

                # Считаем статистику
                total = len(result)
                correct = sum(1 for r in result if r['is_correct'])
                accuracy = round((correct / total) * 100, 1) if total > 0 else 0

                # Формируем ОДИН текст
                text = (
                    f"📊 Статистика по вопросу #{question_id}\n\n"
                    f"Всего ответов: {total}\n"
                    f"Правильно: {correct} ({accuracy}%)\n"
                    f"Неправильно: {total - correct}\n\n"
                    f"Ответы пользователей:\n"
                    f"────────────────────\n"
                )

                for i, entry in enumerate(result, 1):
                    status_emoji = "✅" if entry['is_correct'] else "❌"
                    # Красивая дата (убираем миллисекунды и Z)
                    answered_at = entry['answered_at'].replace('Z', '').split('.')[0]
                    time_str = answered_at.replace('T', ' ')

                    text += (
                        f"{i}. @{entry['username']}\n"
                        f"   Ответ: {entry['user_answer']}\n"
                        f"   {status_emoji} {'Верно' if status_emoji == "✅" else 'Неверно'}\n"
                        f"   {time_str}\n"
                        f"────────────────────\n"
                    )

                # Отправляем одно сообщение
                await message.answer(text, parse_mode="Markdown")

    except aiohttp.ClientResponseError as e:
        await message.answer(f"Ошибка сервер, пожалуйста, попробуйте позже")
    except Exception as e:
        await message.answer("Произошла ошибка при загрузке статистики. Попробуйте позже.")
