from API.routers.users_router.users_schemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from JWT.auth import require_role, get_current_user


users_router = APIRouter(
    prefix= '/users',
    tags= ['users']
)

@users_router.get('')
async def get_all_users(session: AsyncSession = Depends(get_async_session),
                        current_user: Users = Depends(require_role('Админ'))):
    result = await session.scalars(select(Users))
    result = result.all()
    return result

@users_router.get('/me', response_model= User_Out)
async def get_users_info(current_user: Users = Depends(get_current_user)):
    return User_Out.model_validate(current_user)


@users_router.post('/create', response_model= ReadUser, status_code= status.HTTP_201_CREATED)
async def create_new_user(data: CreateUser, session: AsyncSession = Depends(get_async_session)):
    double = await session.scalar(select(Users).where(Users.telegram_id == data.telegram_id))
    if double:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= 'Пользователь уже существует!')

    new_user = Users(
        telegram_id = data.telegram_id,
        username = data.username,
        role = data.role,
        is_banned = data.is_banned
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return ReadUser.model_validate(new_user)


@users_router.put('/me/name', response_model= User_Out)
async def change_name(data: ChangeName,
                      session: AsyncSession = Depends(get_async_session),
                      current_user: Users = Depends(get_current_user)):
    current_user.username = data.name
    await session.commit()
    await session.refresh(current_user)

    return User_Out.model_validate(current_user)

@users_router.put('/change/{telegram_id}', response_model= ReadUser)
async def change(id: int,
                 data: Change_User,
                 session: AsyncSession = Depends(get_async_session),
                 current_user = Depends(require_role('Админ'))):

    user = await session.scalar(select(Users).where(Users.telegram_id == id))
    if user is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= 'Пользователь с таким id не найден')

    updated_data = data.model_dump(exclude_unset=True, exclude_none= True)

    for field, value in updated_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return ReadUser.model_validate(user)

@users_router.delete('/hard_del/{telegram_id}', status_code= status.HTTP_204_NO_CONTENT)
async def hard_delete_user(
        telegram_id: int,
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    item_to_del = await session.scalar(select(Users).where(Users.telegram_id == id))
    if item_to_del is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= 'Такого пользователя не существует')

    await session.delete(item_to_del)
    try:
        await session.commit()
    except Exception as e:
        session.rollback()
        print(f"Rollback due to error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during commit")

    return

@users_router.delete('/soft_del',
                     status_code = status.HTTP_204_NO_CONTENT,
                     )
async def soft_delete_user(
        current_user = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)):
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or already deleted"
        )
    await session.commit()
    return {'message': 'Вы удалили аккаунт! Для его восстановления используйте'}
@users_router.put('/restore_user', response_model= ReadUser)
async def restore_user(
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(get_current_user)):
    telegram_id = current_user.telegram_id

    user = await session.scalar(
        select(Users).where(
            Users.by_telegram_id(telegram_id),
            Users.non_active()
        )
    )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not deleted"
        )

    user.deleted_at = None
    await session.commit()
    await session.refresh(user)
    
    return ReadUser.model_validate(user)

@users_router.get('/{telegram_id}')
async def get_user(telegram_id: int,
                   session: AsyncSession = Depends(get_async_session)):
    result = await session.scalar(select(Users).where(Users.by_telegram_id(telegram_id)))
    if result is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= f'Пользователь с таким telegram_id не найден: {telegram_id}')
    return result