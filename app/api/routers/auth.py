from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.core.JWT.token_shemas import Token, Telegram_Login
from app.services.auth import AuthService


authorization_router = APIRouter(prefix = '/auth', tags= ['auth'])


@authorization_router.post('/login', response_model= Token)
async def login(
        data: Telegram_Login,
        session: AsyncSession = Depends(get_async_session)
):
    return await AuthService.login(data = data, session = session)