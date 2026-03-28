from API.routers.users_router.users_schemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from JWT.auth import require_role, get_current_user
import logging

logger = logging.getLogger(__name__)

users_router = APIRouter(
    prefix= '/users',
    tags= ['users']
)

@users_router.get('')
async def get_all_users(session: AsyncSession = Depends(get_async_session),
                        current_user: Users = Depends(require_role('Админ'))):
    logger.info('Получение информации о всех пользователях')
    result = await session.scalars(select(Users))
    result = result.all()

    if not result:
        logger.error('В БД нет пользователей')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='В базе ещё нет пользователей')

    logger.info(f'Данные о пользователях успешно получены: {len(result)} записей')
    return result

@users_router.get('/me', response_model= User_Out)
async def get_users_info(current_user: Users = Depends(get_current_user)):
    logger.info('Получение информации о себе пользователем %s', current_user.telegram_id)
    return User_Out.model_validate(current_user)


@users_router.post('/create', response_model= ReadUser, status_code= status.HTTP_201_CREATED)
async def create_new_user(data: CreateUser, session: AsyncSession = Depends(get_async_session)):
    logger.info('Проверка на существование пользователя: %s', data.telegram_id)
    double = await session.scalar(select(Users).where(Users.telegram_id == data.telegram_id))
    if double:
        logger.error('Пользователь с таким telegram_id: %s уже существует!', data.telegram_id)
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= 'Пользователь уже существует!')

    logger.info('Создание нового пользователя')
    new_user = Users(
        telegram_id = data.telegram_id,
        username = data.username,
        role = data.role,
        is_banned = data.is_banned
    )

    try:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info('Пользователь %s успешно создан!', data.telegram_id)
    except Exception as e:
        logger.exception('Ошибка создания пользователя %s', data.telegram_id)
        raise HTTPException(status_code=500, detail='Ошибка сервера')

    return ReadUser.model_validate(new_user)


@users_router.put('/me/name', response_model= User_Out)
async def change_name(data: ChangeName,
                      session: AsyncSession = Depends(get_async_session),
                      current_user: Users = Depends(get_current_user)):
    logger.info('Смена имени пользователя %s', current_user.telegram_id)
    try:
        current_user.username = data.name
        await session.commit()
        await session.refresh(current_user)
        logger.info('Успешная смена имени пользователя %s', current_user.telegram_id)
    except Exception as e:
        logger.exception('Ошибка изменения имени пользователя %s', current_user.telegram_id)
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail= 'Ошибки сервера')
    return User_Out.model_validate(current_user)

@users_router.put('/change/{telegram_id}', response_model= ReadUser)
async def change(telegram_id: int,
                 data: Change_User,
                 session: AsyncSession = Depends(get_async_session),
                 current_user = Depends(require_role('Админ'))):
    logger.info('Изменение данных пользователя %s', telegram_id)
    user = await session.scalar(select(Users).where(Users.telegram_id == telegram_id))
    if user is None:
        logger.exception('Пользователя с таким id: %s, не существует!', telegram_id)
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= 'Пользователь с таким telegram_id не найден')

    updated_data = data.model_dump(exclude_unset=True, exclude_none= True)

    for field, value in updated_data.items():
        setattr(user, field, value)

    try:
        await session.commit()
        await session.refresh(user)
        logger.info('Успешное изменение данных о пользователе %s', telegram_id)
    except Exception as e:
        logger.exception('Ошибка изменения данных пользователя %s', telegram_id)

    return ReadUser.model_validate(user)

@users_router.delete('/hard_del/{telegram_id}', status_code= status.HTTP_204_NO_CONTENT)
async def hard_delete_user(
        telegram_id: int,
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(require_role('Админ'))):
    logger.info('Удаление пользователя %s', telegram_id)
    item_to_del = await session.scalar(select(Users).where(Users.telegram_id == id))
    if item_to_del is None:
        logger.error('Такого пользователя не существует %s', telegram_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= 'Такого пользователя не существует')

    await session.delete(item_to_del)
    try:
        await session.commit()
        logger.info('Успешное удаление пользователя: %s', telegram_id)
    except Exception as e:
        await session.rollback()
        logger.exception('Ошибка при удалении пользователя %s', telegram_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during commit")

    return

@users_router.delete('/soft_del',
                     status_code = status.HTTP_204_NO_CONTENT,
                     )
async def soft_delete_user(
        current_user: Users = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)):
    logger.info('Soft delete пользователя %s', current_user.telegram_id)
    telegram_id = current_user.telegram_id
    result = await session.execute(
        update(Users)
        .where(
            Users.by_telegram_id(telegram_id),
               Users.active()
           ).values(deleted_at = datetime.now(timezone.utc))
        .returning(Users.telegram_id)
    )

    if not result:
        logger.error('Пользователь %s не найден', current_user.telegram_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or already deleted"
        )
    await session.commit()
    logger.info('Успешный Soft delete пользователя %s', current_user.telegram_id)
    return
@users_router.put('/restore_user', response_model= ReadUser)
async def restore_user(
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(get_current_user)):
    logger.info('Восстановление пользователя %s', current_user.telegram_id)
    telegram_id = current_user.telegram_id

    user = await session.scalar(
        select(Users).where(
            Users.by_telegram_id(telegram_id),
            Users.non_active()
        )
    )
    
    if user is None:
        logger.warning('Пользователь %s не найден', current_user.telegram_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not deleted"
        )

    user.deleted_at = None
    try:
        await session.commit()
        await session.refresh(user)
        logger.info('Успешное восстановление пользователя %s', current_user.telegram_id)
    except Exception as e:
        await session.rollback()
        logger.exception('Ошибка при восстановлении пользователя %s', telegram_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка сервера")
    return ReadUser.model_validate(user)

@users_router.get('/{telegram_id}')
async def get_user(telegram_id: int,
                   session: AsyncSession = Depends(get_async_session)):
    logger.info('Получение данных о пользователе %s', telegram_id)
    result = await session.scalar(select(Users).where(Users.by_telegram_id(telegram_id)))
    if result is None:
        logger.error('Пользователь %s не найден', telegram_id)
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= f'Пользователь с таким telegram_id не найден: {telegram_id}')
    logger.info('Данные о пользователе %s успешно получены', telegram_id)
    return result