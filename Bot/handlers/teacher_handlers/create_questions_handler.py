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
questions_router = Router()

# Константы валидации
MAX_QUESTION_LENGTH = 500
MIN_QUESTION_LENGTH = 10
MAX_ANSWER_LENGTH = 200
MIN_ANSWER_LENGTH = 1
MAX_OPTIONS = 8
MIN_OPTIONS = 2
MAX_TOPIC_LENGTH = 100
MAX_OPTION_LENGTH = 100

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
    confirm_cancel = State()  # Для подтверждения отмены


async def edit_or_send_message(
    message_or_query: Message | CallbackQuery,
    state: FSMContext,
    text: str,
    reply_markup = None
) -> Message | None:

    data = await state.get_data()
    step_msg_id = data.get('step_msg_id')
    
    try:
        if isinstance(message_or_query, Message):
            chat_id = message_or_query.chat.id
            bot = message_or_query.bot
            message = message_or_query
        else:  # CallbackQuery
            chat_id = message_or_query.message.chat.id
            bot = message_or_query.bot
            message = message_or_query.message
        
        if step_msg_id:
            # Пытаемся отредактировать как текстовое сообщение
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=step_msg_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception:
                # Если это сообщение с фото/медиа, редактируем caption
                try:
                    await bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=step_msg_id,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode="HTML"
                    )
                except Exception:
                    # Если ничего не сработало, удаляем старое и отправляем новое
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=step_msg_id)
                    except Exception:
                        pass
                    
                    msg = await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
                    await state.update_data(step_msg_id=msg.message_id)
                    return msg
            return None
        else:
            if isinstance(message_or_query, Message):
                msg = await message_or_query.answer(text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                msg = await message_or_query.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
            
            await state.update_data(step_msg_id=msg.message_id)
            return msg
    except Exception as e:
        print('Ошибка сервера, пожалуйста, попробуйте позже')
        if isinstance(message_or_query, Message):
            msg = await message_or_query.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            msg = await message_or_query.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        await state.update_data(step_msg_id=msg.message_id)
        return msg


async def delete_user_message(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


def get_difficulty_name(difficulty: int) -> str:
    """Возвращает название сложности"""
    names = {
        1: "🟢 Легкий",
        2: "🟡 Простой",
        3: "🟠 Средний",
        4: "🔴 Сложный",
        5: "⚫ Эксперт"
    }
    return names.get(difficulty, "Неизвестно")


async def go_to_step(callback: CallbackQuery, state: FSMContext, target_step: int):
    data = await state.get_data()
    
    if target_step == 1:
        msg = format_step_message(
            1,
            "Выберите тип вопроса",
            "Вы можете создать вопрос с вариантами ответов или с открытым ответом"
        )
        await edit_or_send_message(callback, state, msg, get_markup_question_type())
        await state.set_state(QuestionState.question_type)
    
    elif target_step == 2:
        print_type = "С вариантами ответов" if data.get('question_type') == 'multiple_choice' else 'Свободный ответ'
        msg = format_step_message(
            2,
            "Введите текст вопроса",
            f"Тип выбран: <b>{print_type}</b>\n\n"
            f"Требования:\n"
            f"  • Минимум {MIN_QUESTION_LENGTH} символов\n"
            f"  • Максимум {MAX_QUESTION_LENGTH} символов\n"
            f"  • Вопрос должен быть понятным и корректным"
        )
        await edit_or_send_message(callback, state, msg, get_markup_back_cancel())
        await state.set_state(QuestionState.text)
    
    elif target_step == 3:
        msg = format_step_message(
            3,
            "Укажите тему вопроса",
            f"Текст принят: <code>{data.get('text', '')[:50]}...</code>\n\n"
            f"Введите тему (например: 'История России', 'Наполеоновские войны')\n"
            f"Или напишите '-' чтобы пропустить этот шаг"
        )
        await edit_or_send_message(callback, state, msg, get_markup_back_cancel())
        await state.set_state(QuestionState.topic)
    
    elif target_step == 4:
        final_topic = data.get('topic')
        msg = format_step_message(
            4,
            "Выберите сложность",
            f"Тема: {'Не указана' if not final_topic else f'<code>{final_topic}</code>'}\n\n"
            f"Сложность определяет уровень вопроса для учащихся"
        )
        await edit_or_send_message(callback, state, msg, get_markup_back_cancel_difficulty())
        await state.set_state(QuestionState.difficulty)
    
    elif target_step == 5:
        if data.get('question_type') == 'multiple_choice':
            msg = format_step_message(
                5,
                "Введите варианты ответов",
                f"Сложность: <b>{get_difficulty_name(data.get('difficulty', 1))}</b>\n\n"
                f"Правила:\n"
                f"  • По одному варианту в каждом сообщении\n"
                f"  • Минимум {MIN_OPTIONS}, максимум {MAX_OPTIONS} вариантов\n"
                f"  • Каждый вариант до {MAX_OPTION_LENGTH} символов\n\n"
                f"Когда закончите — напишите <b>готово</b>"
            )
            kb = get_markup_back_cancel()
        else:
            msg = format_step_message(
                5,
                "Введите правильный ответ",
                f"Сложность: <b>{get_difficulty_name(data.get('difficulty', 1))}</b>\n\n"
                f"Укажите корректный ответ на вопрос."
            )
            kb = get_markup_back_cancel()
        
        await edit_or_send_message(callback, state, msg, kb)
        if data.get('question_type') == 'multiple_choice':
            await state.set_state(QuestionState.options)
        else:
            await state.set_state(QuestionState.correct_answer)
    
    elif target_step == 6:
        msg = format_step_message(
            6,
            "Добавьте картинку (опционально)",
            f"✅ Вопрос заполнен:\n\n"
            f"  📝 <b>Тип:</b> {'С вариантами ответов' if data.get('question_type') == 'multiple_choice' else 'Свободный ответ'}\n"
            f"  ❓ <b>Текст:</b> {data.get('text', '')[:100]}...\n"
            f"  🏷️ <b>Тема:</b> {data.get('topic') if data.get('topic') else 'Не указана'}\n"
            f"  ⚡ <b>Сложность:</b> {get_difficulty_name(data.get('difficulty', 1))}\n"
            f"  ✅ <b>Ответ:</b> {data.get('correct_answer', '')}\n\n"
            f"Хотите добавить картинку к вопросу?"
        )
        await edit_or_send_message(callback, state, msg, get_markup_photo())
        await state.set_state(QuestionState.image)


def format_step_message(step: int, title: str, instruction: str, current_value: str | None = None) -> str:
    step_names = {
        1: "Выбор типа вопроса",
        2: "Текст вопроса",
        3: "Тема",
        4: "Сложность",
        5: "Ответ",
        6: "Картинка",
        7: "Статус"
    }
    
    emoji = get_step_emoji(step)
    progress = get_progress_text(step)
    step_name = step_names.get(step, "")
    
    message = f"{progress} {emoji} <b>{step_name}</b>\n\n"
    message += f"ℹ️ {instruction}"
    
    if current_value:
        message += f"\n\n📌 Текущее значение: <code>{current_value}</code>"
    
    return message


async def show_preview(message_or_query: Message | CallbackQuery, state: FSMContext, show_nav: bool = True):
    data = await state.get_data()

    print_type = "С вариантами ответов" if data['question_type'] == 'multiple_choice' else 'Свободный ответ'

    preview_text = (
        f"{get_progress_text(7)} {get_step_emoji(7)} <b>Превью вопроса</b>\n\n"
        f"📝 <b>Тип:</b> {print_type}\n"
        f"❓ <b>Текст:</b> {data['text']}\n"
        f"🏷️ <b>Тема:</b> {data.get('topic') if data.get('topic') else 'Не указана'}\n"
        f"⚡ <b>Сложность:</b> {data['difficulty']}\n"
        f"✅ <b>Правильный ответ:</b> <code>{data['correct_answer']}</code>\n"
    )

    if data["question_type"] == "multiple_choice":
        preview_text += "\n🔤 <b>Варианты ответов:</b>\n" + "\n".join(f"  • {opt}" for opt in data.get("options", []))

    if show_nav:
        keyboard = get_markup_status()
    else:
        keyboard = None

    image_file_id = data.get('image')

    if image_file_id:
        if isinstance(message_or_query, CallbackQuery):
            try:
                await message_or_query.message.edit_media(
                    media=types.InputMediaPhoto(
                        media=image_file_id,
                        caption=preview_text + "\n\nВыберите статус:",
                        parse_mode="HTML"
                    ),
                    reply_markup=keyboard
                )
            except Exception:
                await message_or_query.message.answer_photo(
                    photo=image_file_id,
                    caption=preview_text + "\n\nВыберите статус:",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            chat_id = message_or_query.chat.id
            bot = message_or_query.bot
            step_msg_id = data.get('step_msg_id')
            
            if step_msg_id:
                try:
                    await bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=step_msg_id,
                        media=types.InputMediaPhoto(
                            media=image_file_id,
                            caption=preview_text + "\n\nВыберите статус:",
                            parse_mode="HTML"
                        ),
                        reply_markup=keyboard
                    )
                except Exception:
                    new_msg = await message_or_query.answer_photo(
                        photo=image_file_id,
                        caption=preview_text + "\n\nВыберите статус:",
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    await state.update_data(step_msg_id=new_msg.message_id)
            else:
                new_msg = await message_or_query.answer_photo(
                    photo=image_file_id,
                    caption=preview_text + "\n\nВыберите статус:",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                await state.update_data(step_msg_id=new_msg.message_id)
    else:
        await edit_or_send_message(message_or_query, state, preview_text + "\n\nВыберите статус:", keyboard)

    await state.set_state(QuestionState.status)

@questions_router.message(Command('add_question'))
async def add_question(message: Message, state: FSMContext):
    if not await check_user_has_role(message, state):
        return

    msg = format_step_message(
        1,
        "Выберите тип вопроса",
        "Вы можете создать вопрос с вариантами ответов или с открытым ответом"
    )
    
    sent_msg = await message.answer(msg, reply_markup=get_markup_question_type(), parse_mode= 'HTML')
    await state.update_data(step_msg_id=sent_msg.message_id)
    await state.set_state(QuestionState.question_type)

@questions_router.callback_query(StateFilter(QuestionState.question_type), F.data.in_(['multiple_choice', 'free_text']))
async def fill_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    q_type = 'multiple_choice' if callback.data == 'multiple_choice' else 'free_text'
    print_type = "С вариантами ответов" if q_type == 'multiple_choice' else 'Свободный ответ'
    await state.update_data(question_type = q_type)
    
    msg = format_step_message(
        2,
        "Введите текст вопроса",
        f"Тип выбран: <b>{print_type}</b>\n\n"
        f"Требования:\n"
        f"  • Минимум {MIN_QUESTION_LENGTH} символов\n"
        f"  • Максимум {MAX_QUESTION_LENGTH} символов\n"
        f"  • Вопрос должен быть понятным и корректным"
    )
    
    await edit_or_send_message(callback, state, msg, get_markup_back_cancel())
    await state.set_state(QuestionState.text)

@questions_router.callback_query(StateFilter(QuestionState.question_type), F.data == 'cancel')
async def cancel_create_questions(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "❌ Создание вопроса отменено.\n"
        "Вы можете начать заново с команды /add_question"
    )
    await state.clear()

@questions_router.message(StateFilter(QuestionState.text))
async def fill_text(message: Message, state: FSMContext):
    text = message.text.strip()
    
    await delete_user_message(message)
    
    # Валидация
    if not text:
        error_msg = (
            "❌ Ошибка валидации\n\n"
            f"Текст вопроса не может быть пустым. Попробуйте снова:"
        )
        await edit_or_send_message(message, state, error_msg)
        return
    
    if len(text) < MIN_QUESTION_LENGTH:
        error_msg = (
            f"⚠️ Текст слишком короткий\n\n"
            f"Минимум {MIN_QUESTION_LENGTH} символов, сейчас: {len(text)}\n"
            f"Пожалуйста, расширьте вопрос."
        )
        await edit_or_send_message(message, state, error_msg)
        return
    
    if len(text) > MAX_QUESTION_LENGTH:
        error_msg = (
            f"⚠️ Текст слишком длинный\n\n"
            f"Максимум {MAX_QUESTION_LENGTH} символов, сейчас: {len(text)}\n"
            f"Пожалуйста, сократите вопрос."
        )
        await edit_or_send_message(message, state, error_msg)
        return

    await state.update_data(text = text)
    
    msg = format_step_message(
        3,
        "Укажите тему вопроса",
        f"Текст принят: <code>{text[:50]}...</code>\n\n"
        f"Введите тему (например: 'История России', 'Наполеоновские войны')\n"
        f"Или напишите '-' чтобы пропустить этот шаг"
    )
    
    await edit_or_send_message(message, state, msg, get_markup_back_cancel())
    await state.set_state(QuestionState.topic)

@questions_router.message(QuestionState.topic)
async def fill_topic(message: Message, state: FSMContext):
    topic = message.text.strip()
    
    await delete_user_message(message)
    
    # Валидация
    if topic != '−' and topic != '-' and len(topic) > MAX_TOPIC_LENGTH:
        error_msg = (
            f"⚠️ Тема слишком длинная\n\n"
            f"Максимум {MAX_TOPIC_LENGTH} символов, сейчас: {len(topic)}\n"
            f"Пожалуйста, сократите или напишите '−' чтобы пропустить."
        )
        await edit_or_send_message(message, state, error_msg)
        return
    
    final_topic = None if topic in ('-', '−') else topic
    await state.update_data(topic = final_topic)
    
    msg = format_step_message(
        4,
        "Выберите сложность",
        f"Тема: {'Не указана' if not final_topic else f'<code>{final_topic}</code>'}\n\n"
        f"Сложность определяет уровень вопроса для учащихся"
    )
    
    await edit_or_send_message(message, state, msg, get_markup_back_cancel_difficulty())
    await state.set_state(QuestionState.difficulty)

@questions_router.callback_query(StateFilter(QuestionState.difficulty), F.data.in_(['difficulty_1', 'difficulty_2', 'difficulty_3', 'difficulty_4', 'difficulty_5']))
async def fill_difficulty(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    difficulty = int(callback.data.split('_')[1])
    difficulty_names = {
        1: "🟢 Легкий",
        2: "🟡 Простой",
        3: "🟠 Средний",
        4: "🔴 Сложный",
        5: "⚫ Эксперт"
    }
    
    await state.update_data(difficulty = difficulty)

    data = await state.get_data()
    if data['question_type'] == 'multiple_choice':
        msg = format_step_message(
            5,
            "Введите варианты ответов",
            f"Сложность: <b>{difficulty_names[difficulty]}</b>\n\n"
            f"Правила:\n"
            f"  • По одному варианту в каждом сообщении\n"
            f"  • Минимум {MIN_OPTIONS}, максимум {MAX_OPTIONS} вариантов\n"
            f"  • Каждый вариант до {MAX_OPTION_LENGTH} символов\n\n"
            f"Когда закончите — напишите <b>готово</b>"
        )
        await edit_or_send_message(callback, state, msg, get_markup_back_cancel())
        await state.set_state(QuestionState.options)
    else:
        msg = format_step_message(
            5,
            "Введите правильный ответ",
            f"Сложность: <b>{difficulty_names[difficulty]}</b>\n\n"
            f"Укажите корректный ответ на вопрос."
        )
        await edit_or_send_message(callback, state, msg, get_markup_back_cancel())
        await state.set_state(QuestionState.correct_answer)
@questions_router.callback_query(StateFilter(QuestionState.difficulty))
async def error_difficulty(callback: CallbackQuery):
    await callback.answer("Пожалуйста, выберите сложность из предложенных вариантов")
    

@questions_router.message(StateFilter(QuestionState.options))
async def fill_options(message: Message, state: FSMContext):
    data = await state.get_data()
    options = data.get('options', [])

    await delete_user_message(message)

    if data.get("question_type") != "multiple_choice":
        error_msg = "❌ Ошибка: для этого типа вопроса варианты не нужны."
        await edit_or_send_message(message, state, error_msg)
        await state.set_state(QuestionState.correct_answer)
        return

    text = message.text.strip().lower()

    if text == 'готово':
        if len(options) < MIN_OPTIONS:
            error_msg = (
                f"❌ Недостаточно вариантов\n\n"
                f"Нужно минимум {MIN_OPTIONS} вариантов, сейчас у вас: {len(options)}\n"
                f"Пожалуйста, добавьте ещё варианты или напишите 'готово' когда будет достаточно."
            )
            await edit_or_send_message(message, state, error_msg)
            return

        await state.update_data(options = options)
        
        msg = format_step_message(
            5,
            "Выберите правильный ответ",
            f"Введено {len(options)} вариантов ✅\n\n"
            f"Укажите, какой из вариантов является правильным ответом:"
        )

        options_text = "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options))
        
        await edit_or_send_message(message, state, msg + f"\n\n🔤 <b>Варианты:</b>\n{options_text}")
        await state.set_state(QuestionState.correct_answer)
        return

    if len(options) >= MAX_OPTIONS:
        error_msg = (
            f"⚠️ Максимум вариантов достигнут\n\n"
            f"Вы можете добавить максимум {MAX_OPTIONS} вариантов.\n"
            f"Пожалуйста, напишите 'готово' чтобы продолжить."
        )
        await edit_or_send_message(message, state, error_msg)
        return
    
    if len(text) < MIN_ANSWER_LENGTH or len(text) > MAX_OPTION_LENGTH:
        error_msg = (
            f"⚠️ Вариант ответа не подходит\n\n"
            f"Требования: от {MIN_ANSWER_LENGTH} до {MAX_OPTION_LENGTH} символов\n"
            f"Текущий размер: {len(text)} символов\n"
            f"Пожалуйста, исправьте и попробуйте снова."
        )
        await edit_or_send_message(message, state, error_msg)
        return
    
    options.append(text)

    preview_text = (
            f"{get_progress_text(5)} {get_step_emoji(5)} <b>Варианты ответов</b>\n\n" +
            "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options)) +
            f"\n\n📊 <b>Статус:</b> {len(options)}/{MAX_OPTIONS}\n\n"
            "➕ Добавьте следующий вариант или напишите <b>готово</b> чтобы закончить"
    )

    await edit_or_send_message(message, state, preview_text)
    await state.update_data(options = options)

@questions_router.message(StateFilter(QuestionState.correct_answer))
async def fill_correct_answer(message: Message, state: FSMContext):
    correct = message.text.strip()
    data = await state.get_data()

    await delete_user_message(message)

    # Валидация
    if not correct:
        error_msg = "❌ Ошибка: ответ не может быть пустым."
        await edit_or_send_message(message, state, error_msg)
        return
    
    if len(correct) > MAX_ANSWER_LENGTH:
        error_msg = (
            f"⚠️ Ответ слишком длинный\n\n"
            f"Максимум {MAX_ANSWER_LENGTH} символов, сейчас: {len(correct)}"
        )
        await edit_or_send_message(message, state, error_msg)
        return

    if data['question_type'] == 'multiple_choice':
        if correct not in data.get('options', []):
            options_text = "\n".join(f"  • {opt}" for opt in data.get('options', []))
            error_msg = (
                f"❌ Ошибка валидации\n\n"
                f"Правильный ответ должен быть <b>одним из вариантов</b> ниже:\n\n"
                f"{options_text}\n\n"
                f"Пожалуйста, выберите один из предложенных вариантов."
            )
            await edit_or_send_message(message, state, error_msg)
            return

    await state.update_data(correct_answer = correct)

    topic = data.get('topic', 'не указана')
    print_type = "С вариантами ответов" if data['question_type'] == 'multiple_choice' else 'Свободный ответ'

    msg = format_step_message(
        6,
        "Добавьте картинку (опционально)",
        f"✅ Вопрос заполнен:\n\n"
        f"  📝 <b>Тип:</b> {print_type}\n"
        f"  ❓ <b>Текст:</b> {data['text'][:100]}...\n"
        f"  🏷️ <b>Тема:</b> {topic if data.get('topic') else 'Не указана'}\n"
        f"  ⚡ <b>Сложность:</b> {data['difficulty']}\n"
        f"  ✅ <b>Ответ:</b> {correct}\n\n"
        f"Хотите добавить картинку к вопросу?"
    )

    await edit_or_send_message(message, state, msg, get_markup_photo())
    await state.set_state(QuestionState.image)

@questions_router.callback_query(StateFilter(QuestionState.image), F.data.in_(['add_image', 'skip_image']))
async def fill_image(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data == 'skip_image':
        await state.update_data(image = None)
        await show_preview(callback, state)
        return

    if callback.data == 'add_image':
        msg = format_step_message(
            6,
            "Загрузите картинку",
            "Отправьте фото к вопросу.\n\n"
            "Поддерживаемые форматы: JPG, PNG\n"
            "Максимальный размер: 5 МБ"
        )
        
        await edit_or_send_message(callback, state, msg)
        return

@questions_router.message(StateFilter(QuestionState.image), F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id

    await delete_user_message(message)

    await state.update_data(image = file_id)
    
    await show_preview(message, state)

@questions_router.callback_query(StateFilter(QuestionState.image), F.data == 'photo_cancel')
async def photo_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "❌ Создание вопроса отменено.\n"
        "Вы можете начать заново с команды /add_question"
    )
    await state.clear()

@questions_router.callback_query(F.data == 'confirm_cancel')
async def confirm_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "❓ Вы уверены, что хотите отменить создание вопроса?\n\n"
        "Все введённые данные будут потеряны.",
        reply_markup=get_markup_cancel_confirm()
    )

@questions_router.callback_query(F.data == 'confirm_cancel_yes')
async def confirm_cancel_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "❌ Создание вопроса отменено.\n\n"
        "Вы можете начать заново с команды /add_question"
    )
    await state.clear()

@questions_router.callback_query(F.data == 'confirm_cancel_no')
async def confirm_cancel_no(callback: CallbackQuery):
    await callback.answer("Продолжаем создание вопроса 👍")

@questions_router.callback_query(F.data.in_(['nav_back', 'nav_back_2', 'nav_back_3', 'nav_back_4', 'nav_back_5', 'nav_back_6']))
async def navigate_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Определяем целевой шаг на основе текущего состояния
    current_state = await state.get_state()
    
    # Карта переходов назад
    back_map = {
        'QuestionState:text': 1,          # С шага "Текст" -> Тип
        'QuestionState:topic': 2,         # С шага "Тема" -> Текст
        'QuestionState:difficulty': 3,    # С шага "Сложность" -> Тема
        'QuestionState:options': 4,       # С шага "Варианты" -> Сложность
        'QuestionState:correct_answer': 4, # С шага "Ответ" -> Сложность
        'QuestionState:image': 5,         # С шага "Картинка" -> Ответ/Варианты
        'QuestionState:status': 6,        # С шага "Статус" -> Картинка
    }
    
    target_step = back_map.get(current_state, 1)
    await go_to_step(callback, state, target_step)

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

    loading_msg = (
        f"⏳ Создание вопроса со статусом <b>{status_ru_dict[status]}</b>...\n\n"
        "Пожалуйста, подождите."
    )
    
    # Редактируем существующее сообщение (удаляем клавиатуру)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    await edit_or_send_message(callback, state, loading_msg)

    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f'{config.api.base_url}/question/new',
                json = schema_class(**payload).model_dump(),
                headers= {"Authorization": f"Bearer {data['user_token']}"}
            )
            resp.raise_for_status()
            response_data = await resp.json()
            question_id = response_data.get('id')

        success_msg = (
            f"✅ <b>Вопрос успешно создан!</b>\n\n"
            f"🆔 <b>ID вопроса:</b> <code>{question_id}</code>\n"
            f"📊 <b>Статус:</b> {status_ru_dict[status]}\n"
            f"📝 <b>Тип:</b> {'С вариантами ответов' if data['question_type'] == 'multiple_choice' else 'Свободный ответ'}\n\n"
            f"📄 <b>Текст вопроса:</b>\n<code>{data['text']}</code>\n\n"
        )
        
        if data['question_type'] == 'multiple_choice':
            options_text = "\n".join(f"  {i+1}. {opt}" for i, opt in enumerate(data.get('options', [])))
            success_msg += (
                f"🔤 <b>Варианты ответов:</b>\n{options_text}\n\n"
            )
        
        success_msg += (
            f"✅ <b>Правильный ответ:</b> <code>{data['correct_answer']}</code>\n\n"
            f"Хотите добавить ещё один вопрос? 📚\n"
            f"Напишите /add_question чтобы начать заново."
        )
        
        await edit_or_send_message(callback, state, success_msg)

    except Exception as e:
        error_msg = ('Ошибка сервера, пожалуйста, попробуйте позже')
        
        await edit_or_send_message(callback, state, error_msg)

    await state.clear()

@questions_router.callback_query(StateFilter(QuestionState.status), F.data == 'status_cancel')
async def cancel_status(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "❌ Создание вопроса отменено.\n"
        "Все введённые данные потеряны.\n\n"
        "Начните заново с /add_question"
    )
    await state.clear()
    return