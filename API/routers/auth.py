from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from Database.database import get_async_session
from JWT.token_shemas import Token, Telegram_Login
from services.auth_service import AuthService


authorization_router = APIRouter(prefix = '/auth', tags= ['auth'])


@authorization_router.post('/login', response_model= Token)
async def login(
        data: Telegram_Login,
        session: AsyncSession = Depends(get_async_session)
):
    return await AuthService.login(data = data, session = session)