from app.repositories import LoginRepository
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.JWT.security import create_access_token
from app.core.JWT.token_shemas import Token, Telegram_Login

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    async def login(data: Telegram_Login, session: AsyncSession) -> Token:
        logger.info("Получение токена пользователем %s", data.telegram_id)

        user = await LoginRepository.get_by_telegram_id(
            telegram_id = data.telegram_id,
            session = session
        )

        if not user:
            logger.warning("Пользователь с id %s не найден", data.telegram_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден",
            )

        if user.is_banned:
            logger.warning("Пользователь с id %s заблокирован", data.telegram_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь заблокирован",
            )

        try:
            access_token = create_access_token(
                data={"telegram_id": user.telegram_id, "role": user.role}
            )
        except Exception:
            logger.exception("Ошибка генерации токена")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка генерации токена",
            )

        return Token(access_token=access_token, token_type="bearer")
