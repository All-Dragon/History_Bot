from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (Message)
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import Bot
from config_app import Config, load_config
from Bot.utils.lexicon import lexicon
from Bot.handlers.registration_handler import registration_router
from Bot.handlers.login_handler import login_router

config: Config = load_config()

bot_token = config.bot.token
admin_ids = config.bot.admin_ids

storage = MemoryStorage()

bot = Bot(token = bot_token)

dp = Dispatcher(storage = storage)
dp.include_router(registration_router)
dp.include_router(login_router)


class RegistrationState(StatesGroup):
    fill_username = State()
    fill_role = State()


@dp.message(CommandStart())
async def start_bot(message: Message) -> None:
    await message.answer(f'Привет, {message.from_user.username}!. Добро пожаловать в History Bot! \nДля получения помощи используй команду /help')

@dp.message(Command('help'))
async def help(message: Message) -> None:
    await message.answer(lexicon['/help'])



async def main() -> None:
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())