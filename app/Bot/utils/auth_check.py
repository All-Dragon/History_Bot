import aiohttp
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.core.config_app import Config, load_config

config: Config = load_config()

async def check_user_has_role(
        message: Message,
        state: FSMContext,
        required_role: list[str] = ["Преподаватель", "Админ"]
) -> bool:
    data = await state.get_data()
    user_token = data.get('user_token')

    if not user_token:
        await message.answer("Сначала войдите в систему командой /login")
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{config.api.base_url}/users/me', headers= {"Authorization": f"Bearer {user_token}"}) as response:
                if response.status == 401:
                    await message.answer("Сессия истекла. Пожалуйста, войдите заново (/login)")
                    await state.clear()
                    return False
                if response.status != 200:
                    await message.answer(f"Ошибка проверки прав (статус {response.status})")
                    return False

                user = await response.json()


                if user.get('role') not in required_role:
                    await message.answer("У вас недостаточно прав для этой команды.")
                    return False

                await state.update_data(user_id=user["id"])

                return True

    except Exception as e:
        await message.answer(f"Ошибка соединения с сервером: {str(e)}")
        return False
