from repositories.ban_router import BanRepository
from services.user_service import UserRepository
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from API.routers.bans_router.bans_schemas import Ban_Info, Ban_Create
from Database.models import Users

logger = logging.getLogger(__name__)

class BanService:
    @staticmethod
    async def all(session: AsyncSession,
                  current_user: Users):
        logger.info('Просмотр всех заблокированных пользователей')
        bans = await BanRepository.get_all(session = session)
        bans = bans.all()
        if not bans:
            logging.warning("Нет заблокированных пользователей")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail= 'Нет забаненых пользователей')
        logger.info('Успешный просмотр всех заблокированных пользователей')
        return bans

    @staticmethod
    async def get_by_id(session: AsyncSession,
                        telegram_id: int):
        logger.info('Получение заблокированного пользователя %s', telegram_id)
        user = await UserRepository.get_by_telegram_id(session = session,
                                                    telegram_id = telegram_id)
        if not user:
            logger.warning('Пользователь %s не найден', telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with telegram_id {telegram_id} not found"
            )

        ban = await BanRepository.get_ban_user(session = session,
                                               user = user)
        if not ban:
            logger.warning('Пользователь %s не забанен', telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with telegram_id {telegram_id} is not banned"
            )
        logger.info('Успешное получение заблокированного пользователя %s', telegram_id)
        return Ban_Info(
            telegram_id=telegram_id,
            reason=ban.reason,
            is_banned=user.is_banned,
            expires_at=ban.expires_at
        )

    @staticmethod
    async def ban(session: AsyncSession,
                  data: Ban_Create):
        logger.info('Блокировка пользователя %s', data.telegram_id)
        user = await UserRepository.get_by_telegram_id(session=session,
                                                    telegram_id=data.telegram_id)
        if not user:
            logger.warning('Пользователь %s не найден', data.telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with telegram_id {data.telegram_id} not found"
            )

        existing_ban = await BanRepository.get_ban_user(session = session,
                                                        user = user)
        if existing_ban:
            logger.warning('Пользователь %s уже забанен', data.telegram_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with telegram_id {data.telegram_id} is already banned"
            )
        try:
            new_bane = await BanRepository.create_ban(session = session,
                                                      user = user,
                                                      data = data)
            logger.info('Пользователь %s успешно заблокирован', data.telegram_id)
        except Exception as e:
            logger.exception('Ошибка при блокировке пользователя %s', data.telegram_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Ошибка сервера')
        return new_bane

    @staticmethod
    async def unban(session: AsyncSession,
                    telegram_id: int,
                    current_user: Users):
        logger.info('Разблокировка пользователя %s', telegram_id)
        user = await UserRepository.get_by_telegram_id(session = session,
                                                    telegram_id = telegram_id)
        if not user:
            logger.warning('Пользователь %s не найден', telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with telegram_id {telegram_id} not found"
            )

        ban = await BanRepository.get_ban_user(session = session,
                                               user = user)
        if not ban:
            logger.warning('Пользователь %s не забанен', telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with telegram_id {telegram_id} is not banned"
            )

        await BanRepository.unban(session = session,
                                  ban = ban,
                                  user = user)
        logger.info('Успешная разблокировка пользователя %s', current_user.telegram_id)
        return