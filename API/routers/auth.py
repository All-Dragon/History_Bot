from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from Database.database import get_async_session
from Database.models import Users
from JWT.token_shemas import Token, Telegram_Login
from JWT.security import create_access_token
from config_app import load_config, Config
import logging

logger = logging.getLogger(__name__)

authorization_router = APIRouter(prefix = '/auth', tags= ['auth'])


@authorization_router.post('/login', response_model= Token)
async def login(
        data: Telegram_Login,
        session: AsyncSession = Depends(get_async_session)
    ):
    logger.info('Получение токена пользователем %s', data.telegram_id)
    user = await session.scalar(
        select(Users).where(Users.telegram_id == data.telegram_id)
    )

    if not user:
        logger.warning('Пользователь с id %s не найден', data.telegram_id)
        raise HTTPException(401, "Пользователь не найден")

    if user.is_banned:
        logger.warning('Пользователь с id %s заблокирован', data.telegram_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь заблокирован"
        )

    try:
        access_token = create_access_token(
            data={"telegram_id": user.telegram_id, "role": user.role}
        )
        logger.info('Успешное получение токена пользователем %s', data.telegram_id)
    except Exception:
        logger.exception('Ошибка генерации токена')
        raise HTTPException(status_code=500, detail="Ошибка генерации токена")

    return Token(access_token=access_token, token_type="bearer")