from app.schemas import User_Out, CreateUser, Change_User, ReadUser, ChangeName
from app.db.database import get_async_session, AsyncSession
from app.db.models import *
from fastapi import Depends, status, APIRouter
from app.core.JWT.auth import require_role, get_current_user
import logging
from app.services.users import UserService

logger = logging.getLogger(__name__)

users_router = APIRouter(
    prefix= '/users',
    tags= ['users']
)

@users_router.get('')
async def get_all_users(session: AsyncSession = Depends(get_async_session),
                        current_user: Users = Depends(require_role('Админ'))):
    logger.info('Получение информации о всех пользователях')
    return await UserService.get_all(session = session)

@users_router.get('/me', response_model= User_Out)
async def get_users_info(current_user: Users = Depends(get_current_user)):
    logger.info('Получение информации о себе пользователем %s', current_user.telegram_id)
    return User_Out.model_validate(current_user)


@users_router.post('/create', response_model= ReadUser, status_code= status.HTTP_201_CREATED)
async def create_new_user(data: CreateUser, session: AsyncSession = Depends(get_async_session)):
    new_user = await UserService.create(data = data, session = session)
    return ReadUser.model_validate(new_user)

@users_router.put('/me/name', response_model= User_Out)
async def change_name(data: ChangeName,
                      session: AsyncSession = Depends(get_async_session),
                      current_user: Users = Depends(get_current_user)):
    updated_user = await UserService.change_name(
        session = session,
        current_user = current_user,
        new_name = data.name
    )
    return User_Out.model_validate(updated_user)

@users_router.put('/change/{telegram_id}', response_model= ReadUser)
async def change(telegram_id: int,
                 data: Change_User,
                 session: AsyncSession = Depends(get_async_session),
                 current_user = Depends(require_role('Админ'))):
    updated_user = await UserService.change(
        telegram_id = telegram_id,
        session = session,
        data = data
    )
    return ReadUser.model_validate(updated_user)

@users_router.delete('/hard_del/{telegram_id}', status_code= status.HTTP_204_NO_CONTENT)
async def hard_delete_user(
        telegram_id: int,
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(require_role('Админ'))):
    return await UserService.hard_delete_user(session = session, telegram_id = telegram_id)

@users_router.delete('/soft_del',
                     status_code = status.HTTP_204_NO_CONTENT,
                     )
async def soft_delete_user(
        current_user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)):
    return await UserService.soft_delete_user(session = session, current_user = current_user)

@users_router.put('/restore_user', response_model= ReadUser)
async def restore_user(
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(get_current_user)):
    user = await UserService.restore_user(session = session, current_user = current_user)
    return ReadUser.model_validate(user)

@users_router.get('/{telegram_id}')
async def get_user(telegram_id: int,
                   session: AsyncSession = Depends(get_async_session),
                   current_user: Users = Depends(require_role('Админ'))):
    return await UserService.get_by_telegram_id(session = session, telegram_id = telegram_id)
