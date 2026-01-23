from aiogram import Dispatcher, Bot, types, F, BaseMiddleware, Router
from aiogram.filters import CommandStart, Command, BaseFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardMarkup,InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, ReplyKeyboardRemove,
                           KeyboardButtonPollType, BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, TelegramObject, User, InputMediaAudio,
                           InputMediaDocument, InputMediaPhoto,
                           InputMediaVideo, PhotoSize)
from aiogram.filters.callback_data import CallbackData
from config_app import Config, load_config
import aiohttp
from typing import Callable, Awaitable, Any
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from Bot.utils.auth_check import check_user_has_role
from Bot.utils.keyboards import (
    get_markup_difficulty, get_markup_question_type, get_markup_status, get_markup_photo,
    get_progress_text, get_step_emoji, get_markup_navigation, get_markup_cancel_confirm,
    get_markup_back_cancel, get_markup_back_cancel_difficulty
)
from API.routers.questions_router.questions_shemas import MultipleChoiceCreate, FreeTextCreate


config: Config = load_config()

get_question_router = Router()


def get_markup_options(options: list[Any]):
    kb_builder = InlineKeyboardBuilder()


    for i, text in enumerate(options):
        kb_builder.button(
            text=text,
            callback_data=AnswerCD(chosen=i).pack()
        )

    kb_builder.adjust(4)

    kb_builder.row(
        InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel_question"
        )
    )

    return kb_builder.as_markup()


def difficult_level(level: int) -> str:
    difficulty_names = {
        1: "🟢 Легкий",
        2: "🟡 Простой",
        3: "🟠 Средний",
        4: "🔴 Сложный",
        5: "⚫ Эксперт"
    }

    dif_level = difficulty_names.get(level)
    return dif_level

class AnswerState(StatesGroup):
    answer_waiting = State()

class AnswerCD(CallbackData, prefix = 'ans'):
    chosen: int # Индекс выбранного варианта


@get_question_router.message(Command('random'))
async def get_random_question(message: Message, state: FSMContext):
    try:

        async with aiohttp.ClientSession() as session:
            async with session.get(f'{config.api.base_url}/question/random') as response:
                if response.status != 200:
                    await message.answer('Ошибка сервера, попробуйте позже!')
                    return

                data = await response.json()

                if not data:
                    await message.answer('Пока нет доступных вопросов')

                await state.update_data(current_question = data)

                q_type = data.get('question_type')
                type_text = "С вариантами ответов" if q_type == 'multiple_choice' else 'Свободный ответ'

                text = (
                    f'Вопрос уровня сложности: {difficult_level(data['difficulty'])}:\n\n'
                    f'{data['text']}\n\n'
                    f'Тип: {type_text}'
                )

                if data['topic']:
                    text += f'\nТема: {data['topic']}'



                if q_type == 'multiple_choice':
                    options = data.get('options', [])
                    keyboard = get_markup_options(options)

                    if data['image_url']:
                        await message.answer_photo(
                            photo = data['image_url'],
                            caption= text,
                            reply_markup= keyboard
                        )
                    else:
                        await message.answer(text = text, reply_markup=keyboard)

                if q_type == 'free_text':

                    if data['image_url']:
                        await message.answer_photo(
                            photo = data['image_url'],
                            caption= text
                        )
                        await state.set_state(AnswerState.answer_waiting)

                    await message.answer(text + "\n\nВаш ответ (введите текст):")
                    await state.set_state(AnswerState.answer_waiting)
    except Exception as e:
        await message.answer(str(e))

@get_question_router.callback_query(AnswerCD.filter())
async def process_multiple_answer(callback: CallbackQuery, state: FSMContext, callback_data: AnswerCD):
    await callback.answer()

    data = await state.get_data()
    questions = data.get("current_question")
    if not questions:
        await callback.message.answer("Вопрос не найден. Запросите новый: /random")
        await state.clear()
        return

    chosen_index = callback_data.chosen
    options = questions.get('options', [])
    if chosen_index >= len(options):
        await callback.message.answer("Вариант не найден.")
        return

    user_answer = options[chosen_index]
    correct = questions['correct_answer']

    if user_answer == correct:
        await callback.message.answer("Правильно! 🎉")
    else:
        await callback.message.answer(f"Неправильно 😔 Правильный ответ: {correct}")

    await state.clear()
    await callback.message.answer("Следующий вопрос? /random")

@get_question_router.callback_query(F.data == 'cancel_question')
async def cancel_questions(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("Вопрос отменён.\nНовый вопрос: /random")


@get_question_router.message(StateFilter(AnswerState.answer_waiting))
async def process_free_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('current_question')
    if not questions:
        await message.answer("Вопрос не найден. Запросите новый: /random")
        await state.clear()
        return

    user_answer = message.text.strip()
    correct = questions['correct_answer']

    if user_answer.lower() == correct.lower():
        await message.answer("Правильно! 🎉")
    else:
        await message.answer(f"Неправильно 😔 Правильный ответ: {correct}")

    await state.clear()
    await message.answer("Следующий вопрос? /random")

