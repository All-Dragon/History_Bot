from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import (Message)
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import Bot
from app.core.config_app import Config, load_config
from app.Bot.handlers.authentication_handlers.login_handler import login_router
from app.Bot.handlers.authentication_handlers.registration_handler import registration_router
from app.Bot.handlers.teacher_handlers.create_questions_handler import questions_router
from app.Bot.handlers.get_questions_handler import get_question_router
from app.Bot.handlers.stats_handler import stats_router
from app.Bot.handlers.teacher_handlers.teacher_func_handler import teacher_func_router

config: Config = load_config()

bot_token = config.bot.token

storage = MemoryStorage()

bot = Bot(token = bot_token)

dp = Dispatcher(storage = storage)
dp.include_router(registration_router)
dp.include_router(login_router)
dp.include_router(questions_router)
dp.include_router(get_question_router)
dp.include_router(stats_router)
dp.include_router(teacher_func_router)

@dp.message(CommandStart())
async def start_bot(message: Message) -> None:
    await message.answer(f'Привет, {message.from_user.username}! Добро пожаловать в History Bot! \nДля получения помощи используй команду /help')

@dp.message(Command('help'))
async def help(message: Message) -> None:
    await message.answer('Помощь')



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
