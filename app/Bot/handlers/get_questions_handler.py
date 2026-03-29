from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardButton, Message, CallbackQuery, BotCommandScopeDefault)
from aiogram.filters.callback_data import CallbackData
from app.core.config_app import Config, load_config
import aiohttp
from typing import Any
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

config: Config = load_config()

get_question_router = Router()

async def delete_user_message(message: Message):
    try:
        await message.delete()
    except Exception:
        pass

def get_markup_options(options: list[Any] = []):
    kb_builder = InlineKeyboardBuilder()



    if len(options) > 1:
        for i, text in enumerate(options):
            kb_builder.button(
                text=text,
                callback_data=AnswerCD(chosen=i).pack()
            )

        kb_builder.adjust(2)

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


async def get_connect_API(link: str, params: dict, message: Message, state: FSMContext):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    link, params = params) as response:

                if response.status == 404:
                    await message.answer("Нет вопросов по заданным параметрам 😔")
                    return

                if response.status != 200:
                    await message.answer('Ошибка сервера, попробуйте позже!')
                    return

                data = await response.json()

                if not data:
                    await message.answer('Пока нет доступных вопросов')
                    return
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
                        await state.set_state(AnswerState.answer_waiting)
                        await message.answer_photo(
                            photo = data['image_url'],
                            caption= text,
                            reply_markup= keyboard
                        )
                    else:
                        await state.set_state(AnswerState.answer_waiting)
                        await message.answer(text = text, reply_markup=keyboard)

                if q_type == 'free_text':

                    if data['image_url']:
                        sent_msg = await message.answer_photo(
                            photo = data['image_url'],
                            caption= text,
                            reply_markup= get_markup_options()
                        )
                        await state.update_data(question_msg_id = sent_msg.message_id)
                        await state.set_state(AnswerState.answer_waiting)

                    else:
                        sent_msg = await message.answer(text + "\n\nВаш ответ (введите текст):", reply_markup= get_markup_options())
                        await state.update_data(question_msg_id = sent_msg.message_id)
                        await state.set_state(AnswerState.answer_waiting)
    except Exception as e:
        await message.answer('Ошибка сервера, пожалуйста, попробуйте позже')

async def save_result(question_id, answer, is_correct, token):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f'{config.api.base_url}/answers/create',
                    json={
                        'question_id': question_id,
                        'answer': answer,
                        'is_correct': is_correct
                    },
                    headers={'Authorization': f'Bearer {token}'}
            ) as resp:

                if resp.status not in (200, 201):
                    error = await resp.text()
                    print(f"Ошибка сохранения ответа: {resp.status} - {error}")
                else:
                    print("Ответ успешно сохранён в базу")
    except Exception as e:
        print(f"Ошибка при отправке ответа на сервер")

async def multiple_answer(callback: CallbackQuery, state: FSMContext, callback_data: AnswerCD):
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
    correct = questions.get('correct_answer')

    q_type = data.get('question_type')
    type_text = "С вариантами ответов" if q_type == 'multiple_choice' else 'Свободный ответ'

    result_text = "Правильно! 🎉" if user_answer == correct else "Неправильно 😔"
    correct_text = f'Правильный ответ: {correct}'

    text = (f'{result_text}\n'
            f'Ваш ответ: {user_answer}\n'
            f'{correct_text}\n\n'
            f'Тип вопроса: {type_text}\n'
            f'Оригинальный вопрос:\n\n'
            f'{questions['text']}')

    if questions.get('image_url'):
        await callback.message.edit_caption(
            caption=text
        )

    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=None
        )

    await save_result(
        question_id= questions.get('id'),
        answer= user_answer,
        is_correct= user_answer == correct,
        token= data.get('user_token')
    )

    await state.clear()

async def free_text(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('current_question')
    if not questions:
        await message.answer("Вопрос не найден. Запросите новый: /random")
        await state.clear()
        return

    user_answer = message.text.strip()
    correct = questions['correct_answer']

    q_type = data.get('question_type')
    type_text = "С вариантами ответов" if q_type == 'multiple_choice' else 'Свободный ответ'

    result_text = "Правильно! 🎉" if user_answer.lower() == correct.lower() else "Неправильно 😔"
    correct_text = f'Правильный ответ: {correct}'
    question_msg_id = data.get('question_msg_id')

    text = (
        f'{result_text}\n'
        f'Ваш ответ: {user_answer}\n'
        f'{correct_text}\n\n'
        f'Тип вопроса: {type_text}\n'
        f'Оригинальный вопрос:\n\n'
        f'{questions['text']}'
    )

    if question_msg_id:
        if questions['image_url']:
            await message.bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=question_msg_id,
                caption=text,
                reply_markup=None
            )
            await delete_user_message(message)

        else:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=question_msg_id,
                text=text,
                reply_markup=None
            )
            await delete_user_message(message)

    await save_result(
        question_id=questions.get('id'),
        answer=user_answer,
        is_correct=user_answer.lower() == correct.lower(),
        token=data.get('user_token')
    )

    await state.clear()

@get_question_router.message(Command('random'))
async def random_question(message: Message, state: FSMContext):

    args = message.text.split()[1:]
    params = {}

    DIFFICULTY_MAP = {
        "1": 1, "easy": 1, "легкий": 1,
        "2": 2, "simple": 2, "простой": 2,
        "3": 3, "medium": 3, "middle": 3, "средний": 3,
        "4": 4, "hard": 4, "сложный": 4,
        "5": 5, "expert": 5, "эксперт": 5,
    }

    if args:
        first = args[0].lower()
        if first in DIFFICULTY_MAP:
            params["difficulty"] = DIFFICULTY_MAP[first]
            if len(args) > 1:
                params["topic"] = " ".join(args[1:])
        else:
            params["topic"] = " ".join(args).title()


    await get_connect_API(f'{config.api.base_url}/question/random', params = params, message= message, state = state)

@get_question_router.message(Command('question'))
async def get_question_by_id(message: Message, state: FSMContext):
    args = message.text.split()[1:]

    if not args or not args[0].isdigit():
        await message.answer("Использование: /question <id>")
        return

    question_id = int(args[0])
    await get_connect_API(f'{config.api.base_url}/question/{question_id}', message=message, state=state)


@get_question_router.callback_query(AnswerCD.filter())
async def process_multiple_answer(callback: CallbackQuery, state: FSMContext, callback_data: AnswerCD):
    await multiple_answer(
                          callback = callback,
                          state = state,
                          callback_data= callback_data
    )


@get_question_router.message(StateFilter(AnswerState.answer_waiting), ~F.text.startswith("/"))
async def process_free_answer(message: Message, state: FSMContext):
    await free_text(message = message, state = state)


@get_question_router.callback_query(StateFilter(AnswerState.answer_waiting), F.data == 'cancel_question')
async def cancel_questions(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "Вопрос отменён.\nНовый вопрос: /random"
    )



