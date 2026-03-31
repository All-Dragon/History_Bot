from app.schemas.bans import *
from app.services.bans import BanService
from app.db.database import get_async_session, AsyncSession
from app.db.models import *
from fastapi import Depends, status, APIRouter
from app.core.JWT.auth import require_role
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
