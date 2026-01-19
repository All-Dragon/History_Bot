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
from Bot.utils.keyboards import get_markup_difficulty, get_markup_question_type, get_markup_status, get_markup_photo
from API.routers.questions_router.questions_shemas import MultipleChoiceCreate, FreeTextCreate

config: Config = load_config()
questions_router = Router()

class QuestionState(StatesGroup):
    question_type = State()
    text = State()
    topic = State()
    difficulty = State()
    options = State() # Только для multiple_choice
    correct_answer = State()
    image = State() # Если будет фотка, необязательное поле
    preview = State()
    status = State()


async def show_preview(message_or_query: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()

    preview_text = (
        f"Предпросмотр вопроса:\n\n"
        f"Тип: {data['question_type'].replace('_', ' ')}\n"
        f"Текст: {data['text']}\n"
        f"Тема: {data.get('topic', 'не указана')}\n"
        f"Сложность: {data['difficulty']}\n"
        f"Правильный ответ: {data['correct_answer']}\n"
    )

    if data["question_type"] == "multiple_choice":
        preview_text += "\nВарианты:\n" + "\n".join(f"• {opt}" for opt in data.get("options", []))

    keyboard = get_markup_status()  # ← кнопки для выбора статуса

    image_file_id = data.get('image')

    if image_file_id:
        # Отправляем фото + текст в caption
        if isinstance(message_or_query, Message):
            await message_or_query.answer_photo(
                photo=image_file_id,
                caption=preview_text + "\n\nВыберите статус и подтвердите создание:",
                reply_markup=keyboard
            )
        else:  # CallbackQuery
            await message_or_query.message.answer_photo(
                photo=image_file_id,
                caption=preview_text + "\n\nВыберите статус и подтвердите создание:",
                reply_markup=keyboard
            )
    else:
        # Без фото — просто текст
        if isinstance(message_or_query, Message):
            await message_or_query.answer(
                preview_text + "\n\nВыберите статус и подтвердите создание:",
                reply_markup=keyboard
            )
        else:  # CallbackQuery
            await message_or_query.message.edit_text(
                preview_text + "\n\nВыберите статус и подтвердите создание:",
                reply_markup=keyboard
            )

    await state.set_state(QuestionState.status)

@questions_router.message(Command('add_questions'))
async def add_question(message: Message, state: FSMContext):
    if not await check_user_has_role(message, state):
        return

    await message.answer('Пожалуйста, выберите тип вопроса:',
                         reply_markup= get_markup_question_type())

    await state.set_state(QuestionState.question_type)

@questions_router.callback_query(StateFilter(QuestionState.question_type), F.data.in_(['multiple_choice', 'free_text']))
async def fill_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    q_type = 'multiple_choice' if callback.data == 'multiple_choice' else 'free_text'
    print_type = "С вариантами ответов" if q_type == 'multiple_choice' else 'Свободный ответ'
    await state.update_data(question_type = q_type)
    await callback.message.answer(f'Тип вопроса: {print_type}\n\nТеперь введите текст вопроса:')
    await state.set_state(QuestionState.text)

@questions_router.callback_query(StateFilter(QuestionState.question_type), F.data == 'cancel')
async def cancel_create_questions(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Создание вопроса отменено.')
    await state.clear()

@questions_router.message(StateFilter(QuestionState.text))
async def fill_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("Текст вопроса не может быть пустым. Попробуйте снова:")
        return

    await state.update_data(text = text)
    await message.answer('Тема вопроса (или отправьте "-", если не нужна):')
    await state.set_state(QuestionState.topic)

@questions_router.message(QuestionState.topic)
async def fill_topic(message: Message, state: FSMContext):
    topic = message.text.strip()
    await state.update_data(topic = None if topic == '-' else topic)
    await message.answer('Выберите сложность вопроса (число от 1 до 5):', reply_markup= get_markup_difficulty())
    await state.set_state(QuestionState.difficulty)

@questions_router.callback_query(StateFilter(QuestionState.difficulty), F.data.in_(['difficulty_1', 'difficulty_2', 'difficulty_3', 'difficulty_4', 'difficulty_5']))
async def fill_difficulty(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    difficulty = int(callback.data.split('_')[1])
    await state.update_data(difficulty = difficulty)

    data = await state.get_data()
    if data['question_type'] == 'multiple_choice':
        await callback.message.answer(
            "Теперь вводите варианты ответов:\n"
            "• По одному варианту в каждом сообщении\n"
            "• Когда закончите — напишите слово «готово»"
        )
        await state.set_state(QuestionState.options)
    else:
        await callback.message.answer('Введите правильный ответ:')
        await state.set_state(QuestionState.correct_answer)
@questions_router.callback_query(StateFilter(QuestionState.difficulty))
async def error_difficulty(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Пожалуйста, выберите вариант из предложенных.')

@questions_router.message(StateFilter(QuestionState.options))
async def fill_options(message: Message, state: FSMContext):
    data = await state.get_data()
    options = data.get('options', [])
    preview_msg_id = data.get('options_preview_msg_id')

    if data.get("question_type") != "multiple_choice":
        await message.answer("Для этого типа вопроса варианты не нужны.")
        await state.set_state(QuestionState.correct_answer)
        return

    text = message.text.strip().lower()
    if text == 'готово':
        if len(options) < 2:
            await message.answer("Нужно минимум 2 варианта. Продолжайте ввод или напишите 'готово' позже.")
            return

        await state.update_data(options = options)
        await message.answer('Введите правильный ответ (должен быть одним из вариантов):')
        await state.set_state(QuestionState.correct_answer)
        return
    options.append(text)

    preview_text = (
            f"Варианты ответов (пока):\n\n" +
            "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options)) +
            f"\n\nВсего: {len(options)} из максимум 8\n"
            "Напишите следующий вариант или «готово»"
    )

    try:
        await message.delete()

        if preview_msg_id:
            # Редактируем существующее сообщение
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=preview_msg_id,
                text=preview_text
            )
        else:
            # Первое сообщение — отправляем новое
            sent_msg = await message.answer(preview_text)
            preview_msg_id = sent_msg.message_id
            await state.update_data(options_preview_msg_id=preview_msg_id)

    except Exception as e:
        # Если редактирование не удалось (редко), просто отправляем новое
        sent_msg = await message.answer(preview_text)
        await state.update_data(options_preview_msg_id=sent_msg.message_id)


    await state.update_data(options = options)

@questions_router.message(StateFilter(QuestionState.correct_answer))
async def fill_correct_answer(message: Message, state: FSMContext):
    correct = message.text.strip()
    data = await state.get_data()

    if data['question_type'] == 'multiple_choice':
        if correct not in data.get('options', []):
            await message.answer("Правильный ответ должен быть одним из введённых вариантов. Попробуйте снова:")
            return

    await state.update_data(correct_answer = correct)

    topic = data.get('topic', 'не указана')

    preview_text = (
        f"Предпросмотр вопроса:\n\n"
        f"Тип: {data['question_type'].replace('_', ' ')}\n"
        f"Текст: {data['text']}\n"
        f"Тема: {"Нет темы" if topic is None else topic}\n"
        f"Сложность: {data['difficulty']}\n"
        f"Правильный ответ: {correct}\n"
    )

    if data["question_type"] == "multiple_choice":
        preview_text += "\nВарианты:\n" + "\n".join(f"• {opt}" for opt in data.get("options", []))



    await message.answer(preview_text)
    await message.answer('Хотите добавить картинку в вопрос?', reply_markup=get_markup_photo())

    await state.set_state(QuestionState.image)

@questions_router.callback_query(StateFilter(QuestionState.image), F.data.in_(['add_image', 'skip_image']))
async def fill_image(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == 'skip_image':
        await state.update_data(image = None)
        await show_preview(callback, state)
        return

    if callback.data == 'add_image':
        await callback.message.edit_text(
            "Отправьте фото к вопросу.\n\n"
            "После отправки бот автоматически продолжит."
        )
        return

@questions_router.message(StateFilter(QuestionState.image), F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id

    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(image = file_id)
    await message.answer('Фото добавлено! Теперь посмотрите на вопрос и выберите статус.')

    await show_preview(message, state)

@questions_router.callback_query(StateFilter(QuestionState.image), F.data == 'photo_cancel')
async def photo_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Создание вопроса отменено.')
    await state.clear()

@questions_router.callback_query(StateFilter(QuestionState.status), F.data.in_(['status_published', 'status_draft', 'status_archived']))
async def fill_status(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    status_dict = {
        "status_draft": "draft",
        "status_published": "published",
        "status_archived": "archived"
    }
    status_ru_dict = {
        'draft': 'Черновик',
        'published': 'Опубликовано',
        'archived': 'В архиве'
    }

    status = status_dict.get(callback.data)

    await state.update_data(status = status)

    data = await state.get_data()

    payload = {
        'text': data['text'],
        'difficulty': data['difficulty'],
        'status': data['status'],
        'question_type': data['question_type'],
        'correct_answer': data['correct_answer']
    }

    if data['topic'] is not None:
        payload['topic'] = data['topic']

    if data['question_type'] == 'multiple_choice':
        payload['options'] = data.get("options", [])
        schema_class = MultipleChoiceCreate
    else:
        schema_class = FreeTextCreate

    if data['image'] is not None:
        payload['image_url'] = data.get('image')
    else:
        payload['image_url'] = None


    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f'{config.api.base_url}/question/new',
                json = schema_class(**payload).model_dump(),
                headers= {"Authorization": f"Bearer {data['user_token']}"}
            )
            resp.raise_for_status()

        await callback.message.answer(
            f"✅ Вопрос успешно создан со статусом **{status_ru_dict[status]}**!\n"
            "Хотите добавить ещё один? Напишите /add_question"
        )

    except Exception as e:
        await callback.message.answer(f"Ошибка при сохранении:\n{str(e)}")

    await state.clear()

@questions_router.callback_query(StateFilter(QuestionState.status), F.data == 'status_cancel')
async def cancel_status(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer('Отмена создания вопроса')
    await state.clear()
    return