from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from Database.database import get_async_session
from Database.models import Users
from JWT.token_shemas import Token, Telegram_Login
from JWT.security import create_access_token
from config_app import load_config, Config

authorization_router = APIRouter(prefix = '/auth', tags= ['auth'])


@authorization_router.post('/login', response_model= Token)
async def login(
        data: Telegram_Login,
        session: AsyncSession = Depends(get_async_session)
    ):
    user = await session.scalar(
        select(Users).where(Users.telegram_id == data.telegram_id)
    )

    if not user:
        raise HTTPException(401, "Пользователь не найден")

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь заблокирован"
        )

    access_token = create_access_token(
        data={"telegram_id": user.telegram_id, "role": user.role}
    )

    return Token(access_token=access_token, token_type="bearer")