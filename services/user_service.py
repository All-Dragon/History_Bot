from repositories.users_router import UserRepository
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from JWT.security import create_access_token
from JWT.token_shemas import Token, Telegram_Login
from API.routers.users_router.users_schemas import CreateUser, User_Out, Change_User

logger = logging.getLogger(__name__)
from Database.models import Users
class UserService:
    @staticmethod
    async def get_all(
            session: AsyncSession):
        logger.info("Получение данных всех пользователей")
        users = await UserRepository.get_all_user(session = session)
        users = users.all()
        if not users:
            logger.error('В БД нет пользователей')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='В базе ещё нет пользователей')
        logger.info(f'Данные о пользователях успешно получены: {len(users)} записей')
        return users

    @staticmethod
    async def get_by_telegram_id(
            session: AsyncSession,
            telegram_id: int
    ):
        logger.info('Получение данных о пользователе %s', telegram_id)
        user = await UserRepository.get_by_telegram_id(session = session, telegram_id = telegram_id)
        if user is None:
            logger.error('Пользователь %s не найден', telegram_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Пользователь с таким telegram_id не найден: {telegram_id}')
        logger.info('Данные о пользователе %s успешно получены', telegram_id)
        return user

    @staticmethod
    async def create(
            session: AsyncSession,
            data: CreateUser
    ):
        logger.info('Проверка на существование пользователя: %s', data.telegram_id)
        user = await UserRepository.get_by_telegram_id(session = session,
                                                       telegram_id= data.telegram_id)
        if user:
            logger.error('Пользователь с таким telegram_id: %s уже существует!', data.telegram_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Пользователь уже существует!')

        new_user = Users(
            telegram_id=data.telegram_id,
            username=data.username,
            role=data.role,
            is_banned=data.is_banned
        )
        try:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            logger.info('Пользователь %s успешно создан!', data.telegram_id)
        except Exception as e:
            logger.exception('Ошибка создания пользователя %s', data.telegram_id)
            raise HTTPException(status_code=500, detail='Ошибка сервера')

        return new_user


    @staticmethod
    async def change_name(
            session: AsyncSession,
            current_user: Users,
            new_name: str
    ):
        logger.info('Смена имени пользователя %s', current_user.telegram_id)

        try:
            user = await UserRepository.change_name(session = session,
                                                    user = current_user,
                                                    new_name = new_name)
            logger.info(
                'Успешная смена имени пользователя %s',
                current_user.telegram_id,)
        except Exception:
            logger.exception(
                'Ошибка изменения имени пользователя %s',
                current_user.telegram_id,)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибки сервера',)
        return user


    @staticmethod
    async def change(
            telegram_id: int,
            session: AsyncSession,
            data: Change_User
    ):
        logger.info('Изменение данных пользователя %s', telegram_id)
        user = await UserRepository.get_by_telegram_id(telegram_id = telegram_id, session = session)

        if not user:
            logger.exception('Пользователя с таким id: %s, не существует!', telegram_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Пользователь с таким telegram_id не найден')

        update_data = data.model_dump(exclude_unset=True, exclude_none= True)
        try:
            user = await UserRepository.change(
                session = session,
                user = user,
                updated_data = update_data
            )
            logger.info(
                'Успешное изменение данных о пользователе %s',
                telegram_id
            )
        except Exception:
            logger.exception(
                'Ошибка изменения данных пользователя %s',
                telegram_id
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Ошибка сервера'
            )

        return user

    @staticmethod
    async def restore_user(
            session: AsyncSession,
            current_user: Users
    ):
        logger.info('Восстановление пользователя %s', current_user.telegram_id)
        user = await UserRepository.get_deleted_user(session = session, telegram_id = current_user.telegram_id)

        if user is None:
            logger.warning('Пользователь %s не найден', current_user.telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or not deleted"
            )

        try:
            restore_user = await UserRepository.restore_user(session = session, user = user)
            logger.info('Успешное восстановление пользователя %s', current_user.telegram_id)
        except Exception as e:
            logger.exception('Ошибка при восстановлении пользователя %s', current_user.telegram_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка сервера")

        return restore_user


    @staticmethod
    async def soft_delete_user(
            session: AsyncSession,
            current_user: Users
    ):
        logger.info('Soft delete пользователя %s', current_user.telegram_id)
        user = await UserRepository.get_active_user(session = session, telegram_id = current_user.telegram_id)
        if not user:
            logger.error('Пользователь %s не найден', current_user.telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or already deleted"
            )

        try:
            deleted_user = await UserRepository.soft_delete_user(session = session, user = user)
            logger.info('Успешный Soft delete пользователя %s', current_user.telegram_id)
        except Exception as e:
            logger.exception('Ошибка при удалении пользователя %s', current_user.telegram_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка сервера")
        return

    @staticmethod
    async def hard_delete_user(
            session: AsyncSession,
            telegram_id: int
    ):
        logger.info('Hard delete пользователя %s', telegram_id)
        user = await UserRepository.get_by_telegram_id(session = session, telegram_id = telegram_id)
        if not user:
            logger.error('Пользователь %s не найден', telegram_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or already deleted"
            )

        try:
            deleted_user = await UserRepository.hard_delete_user(session=session, user=user)
            logger.info('Успешный Hard delete пользователя %s', telegram_id)
        except Exception as e:
            logger.exception('Ошибка при удалении пользователя %s', telegram_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка сервера")
        return
