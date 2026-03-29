from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery)
import aiohttp
from aiogram.filters.callback_data import CallbackData
from math import ceil

from app.Bot.utils.auth_check import check_user_has_role
from app.core.config_app import Config, load_config

config: Config = load_config()
teacher_func_router = Router()

difficulty_names = {
        1: "🟢 Легкий",
        2: "🟡 Простой",
        3: "🟠 Средний",
        4: "🔴 Сложный",
        5: "⚫ Эксперт"
    }

class PaginationCallback(CallbackData, prefix = 'pag'):
    action: str
    page: int
    per_page: int = 5
    data_type: str


def get_markup_pagination(
        current_page: int,
        total_items: int,
        per_page: int = 5,
        data_type: str = 'questions'
) -> InlineKeyboardMarkup:

    total_pages = ceil(total_items / per_page)

    keyboard = InlineKeyboardMarkup(inline_keyboard= [])

    row = []

    if current_page > 1:
        row.append(
            InlineKeyboardButton(
                text = '◀️ Назад',
                callback_data= PaginationCallback(
                    action="prev",
                    page=current_page - 1,
                    per_page=per_page,
                    data_type=data_type
                ).pack()
            )
        )

    row.append(
        InlineKeyboardButton(
            text=f"{current_page} / {total_pages}",
            callback_data="ignore"  # просто декоративная кнопка
        )
    )

    if current_page < total_pages:
        row.append(
            InlineKeyboardButton(
                text = 'Вперёд ▶️',
                callback_data= PaginationCallback(
                    action="next",
                    page=current_page + 1,
                    per_page=per_page,
                    data_type=data_type
                ).pack()
            )
        )

    keyboard.inline_keyboard.append(row)
    return keyboard


def paginate_items(items: list, page: int, per_page: int = 5):
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]

class ResultsStates(StatesGroup):
    waiting_results = State()

@teacher_func_router.message(Command('my_questions'))
async def get_all_my_questions(message: Message, state: FSMContext):
    if not await check_user_has_role(message, state, ['Преподаватель', 'Админ']):
        return

    data = await state.get_data()
    token = data.get('user_token')

    if not token:
        await message.answer("Вы не авторизованы. Войдите: /login")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{config.api.base_url}/question/my',
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                if response.status == 401:
                    await message.answer("Сессия истекла. Войдите заново: /login")
                    await state.clear()
                    return

                if response.status == 403:
                    await message.answer("Нет доступа к списку вопросов")
                    return

                if response.status != 200:
                    error_text = await response.text()
                    await message.answer(f"Ошибка сервера: {response.status} — {error_text}")
                    return

                questions = await response.json()

                if not questions:
                    await message.answer("У вас пока нет созданных вопросов.")
                    return

                await state.update_data(my_questions=questions, current_page=1, per_page=5)

                await show_paginated_questions(message, state)

    except Exception as e:
        await message.answer("Произошла ошибка при загрузке вопросов. Попробуйте позже.")


async def show_paginated_questions(message_or_query: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions = data.get('my_questions', [])
    current_page = data.get('current_page', 1)
    per_page = data.get('per_page', 5)

    if not questions:
        text = "У вас пока нет вопросов."
        keyboard = None
    else:
        paginated = paginate_items(questions, current_page, per_page)

        text = (
            f"📚 Ваши вопросы (страница {current_page} из {ceil(len(questions)/per_page)})\n\n"
            f"────────────────────\n"
        )

        for i, q in enumerate(paginated, (current_page-1)*per_page + 1):
            q_type = "С вариантами" if q['question_type'] == 'multiple_choice' else "Свободный ответ"
            has_photo = "📸 Есть фото" if q.get('image_url') else "Без фото"
            short_text = q['text'][:60] + "..." if len(q['text']) > 60 else q['text']

            text += (
                f"{i}. ID: {q['id']}\n"
                f"   {short_text}\n"
                f"   Тема: {q.get('topic', '—')}\n"
                f"   Сложность: {difficulty_names.get(q['difficulty'], '—')}\n"
                f"   Тип: {q_type}\n"
                f"   {has_photo}\n"
                f"   Статус: {q['status'].capitalize()}\n"
                f"────────────────────\n"
            )

        keyboard = get_markup_pagination(current_page, len(questions), per_page, "questions")

    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message_or_query.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@teacher_func_router.callback_query(PaginationCallback.filter(F.data_type == "questions"))
async def process_questions_pagination(callback: CallbackQuery, callback_data: PaginationCallback, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    questions = data.get('my_questions', [])
    current_page = callback_data.page

    await state.update_data(current_page=current_page)

    await show_paginated_questions(callback, state)

@teacher_func_router.message(Command('result'))
async def get_result_question_by_id(message: Message, state: FSMContext):
    if not await check_user_has_role(message, state, ['Преподаватель', 'Админ']):
        return

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
                    await message.answer(f"Ошибка сервера, пожалуйста, попробуйте позже)")
                    return

                answers = await response.json()

                if not answers:
                    await message.answer(f"По вопросу #{question_id} пока никто не ответил.")
                    return

                await state.update_data(
                    current_question_answers=answers,
                    result_page=1,
                    result_per_page=10,
                    result_question_id=question_id
                )


                await show_paginated_answers(message, state)

    except Exception as e:
        await message.answer("Произошла ошибка при загрузке статистики. Попробуйте позже.")


async def show_paginated_answers(message_or_query: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    answers = data.get('current_question_answers', [])
    current_page = data.get('result_page', 1)
    per_page = data.get('result_per_page', 10)
    question_id = data.get('result_question_id')

    if not answers:
        text = f"По вопросу #{question_id} пока никто не ответил."
        keyboard = None
    else:
        paginated = paginate_items(answers, current_page, per_page)

        total = len(answers)
        correct = sum(1 for r in answers if r['is_correct'])
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0

        text = (
            f"📊 Статистика по вопросу #{question_id} (страница {current_page} из {ceil(total/per_page)})\n\n"
            f"Всего ответов: {total}\n"
            f"Правильно: {correct} ({accuracy}%)\n"
            f"Неправильно: {total - correct}\n\n"
            f"Ответы пользователей:\n"
            f"────────────────────\n"
        )

        for i, entry in enumerate(paginated, (current_page-1)*per_page + 1):
            status_emoji = "✅" if entry['is_correct'] else "❌"
            answered_at = entry['answered_at'].replace('Z', '').split('.')[0]
            time_str = answered_at.replace('T', ' ')

            text += (
                f"{i}. {entry['username']}\n"
                f"   Ответ: {entry['user_answer']}\n"
                f"   {status_emoji} {'Верно' if status_emoji == '✅' else 'Неверно'}\n"
                f"   {time_str}\n"
                f"────────────────────\n"
            )

        keyboard = get_markup_pagination(current_page, total, per_page, "answers")

    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message_or_query.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@teacher_func_router.callback_query(PaginationCallback.filter(F.data_type == "answers"))
async def process_answers_pagination(callback: CallbackQuery, callback_data: PaginationCallback, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    current_page = callback_data.page

    await state.update_data(result_page=current_page)

    await show_paginated_answers(callback, state)
