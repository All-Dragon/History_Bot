from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.JWT.security import decode_token
from app.Database.database import get_async_session
from app.Database.models import Users
from app.core.JWT.token_shemas import Token_Data
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()  # Вместо OAuth2PasswordBearer

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        session: AsyncSession = Depends(get_async_session)
):
    token = credentials.credentials
    try:
        token_data = Token_Data(**decode_token(token))
    except Exception as e:
        logger.warning('Невалидный токен: %s', e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if token_data.telegram_id is None:
        logger.warning('Токен не содержит telegram_id')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = await session.scalar(
        select(Users).where(Users.telegram_id == token_data.telegram_id)
    )

    if user is None:
        logger.info('Пользователь не найден: telegram_id=%s', token_data.telegram_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user.is_banned:
        logger.info('Заблокированный пользователь пытается войти: %s', user.telegram_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned"
        )

    logger.debug('Пользователь авторизован: %s', user.telegram_id)
    return user


def require_role(*roles: str):
    async def checker(current_user: Users = Depends(get_current_user)):
        if current_user.role not in roles:
            logger.warning(
                'Доступ запрещён для пользователя %s, роль: %s, требуется: %s',
                current_user.telegram_id, current_user.role, roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}"
            )
        logger.debug('Доступ разрешён для пользователя %s', current_user.telegram_id)
        return current_user
    return checker
