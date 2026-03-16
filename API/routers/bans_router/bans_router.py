from API.routers.bans_router.bans_schemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from JWT.auth import require_role, get_current_user
from datetime import datetime, timezone


bans_router = APIRouter(
    prefix= '/bans',
    tags = ['bans']
)

@bans_router.get('')
async def get_all_bans(session: AsyncSession = Depends(get_async_session),
                       current_user: Users = Depends(require_role('Админ'))):
    result = await session.scalars(select(Ban))
    result = result.all()
    return result

@bans_router.get('/{telegram_id}', response_model=Ban_Info)
async def get_ban(telegram_id: int, 
                  session: AsyncSession = Depends(get_async_session),
                  current_user: Users = Depends(require_role('Админ'))):
    user = await session.scalar(
        select(Users).where(Users.telegram_id == telegram_id)
    )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with telegram_id {telegram_id} not found"
        )
    
    ban = await session.scalar(
        select(Ban).where(Ban.user_id == user.id)
    )
    
    if ban is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with telegram_id {telegram_id} is not banned"
        )
    
    return Ban_Info(
        telegram_id=telegram_id,
        reason=ban.reason,
        is_banned=user.is_banned,
        expires_at=ban.expires_at
    )

@bans_router.post('', response_model=Ban_Read, status_code=status.HTTP_201_CREATED)
async def create_ban(data: Ban_Create,
                     session: AsyncSession = Depends(get_async_session),
                     current_user: Users = Depends(require_role('Админ'))):
    
    user = await session.scalar(
        select(Users).where(Users.telegram_id == data.telegram_id)
    )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with telegram_id {data.telegram_id} not found"
        )

    existing_ban = await session.scalar(
        select(Ban).where(Ban.user_id == user.id)
    )
    
    if existing_ban:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with telegram_id {data.telegram_id} is already banned"
        )

    new_ban = Ban(
        user_id=user.id,
        reason=data.reason,
        expires_at=data.expires_at
    )

    user.is_banned = True
    
    session.add(new_ban)
    await session.commit()
    await session.refresh(new_ban)
    
    return new_ban

@bans_router.delete('/{telegram_id}', status_code=status.HTTP_204_NO_CONTENT)
async def unban_user(telegram_id: int,
                     session: AsyncSession = Depends(get_async_session),
                     current_user: Users = Depends(require_role('Админ'))):
    
    user = await session.scalar(
        select(Users).where(Users.telegram_id == telegram_id)
    )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with telegram_id {telegram_id} not found"
        )
    
    ban = await session.scalar(
        select(Ban).where(Ban.user_id == user.id)
    )
    
    if ban is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with telegram_id {telegram_id} is not banned"
        )

    await session.delete(ban)
    user.is_banned = False
    
    await session.commit()
    
    return
