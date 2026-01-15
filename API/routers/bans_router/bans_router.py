from API.routers.bans_router.bans_schemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter


bans_router = APIRouter(
    prefix= '/bans',
    tags = ['bans']
)

@bans_router.get('')
async def get_all_bans(session: AsyncSession = Depends(get_async_session)):
    result = await session.scalars(select(Ban))
    result = result.all()
    return result

@bans_router.get('/{telegram_id}', response_model=Ban_Read)
async def get_ban(telegram_id: int ,session: AsyncSession = Depends(get_async_session)):
    pass