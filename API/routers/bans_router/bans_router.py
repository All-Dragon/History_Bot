from API.routers.bans_router.bans_schemas import *
from services.ban_service import BanService
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from JWT.auth import require_role, get_current_user
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

bans_router = APIRouter(
    prefix= '/bans',
    tags = ['bans']
)

@bans_router.get('')
async def get_all_bans(session: AsyncSession = Depends(get_async_session),
                       current_user: Users = Depends(require_role('Админ'))):
    return await BanService.all(session = session,
                                current_user = current_user)

@bans_router.get('/{telegram_id}', response_model=Ban_Info)
async def get_ban(telegram_id: int, 
                  session: AsyncSession = Depends(get_async_session),
                  current_user: Users = Depends(require_role('Админ'))):
    return await BanService.get_by_id(session = session,
                                     telegram_id = telegram_id)

@bans_router.post('', response_model=Ban_Read, status_code=status.HTTP_201_CREATED)
async def create_ban(data: Ban_Create,
                     session: AsyncSession = Depends(get_async_session),
                     current_user: Users = Depends(require_role('Админ'))):
    return await BanService.ban(session = session,
                                data = data)

@bans_router.delete('/{telegram_id}', status_code=status.HTTP_204_NO_CONTENT)
async def unban_user(telegram_id: int,
                     session: AsyncSession = Depends(get_async_session),
                     current_user: Users = Depends(require_role('Админ'))):
    return await BanService.unban(session = session,
                                  telegram_id = telegram_id,
                                  current_user = current_user)
