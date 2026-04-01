from app.services import StatService
from app.db.database import get_async_session, AsyncSession
from app.db.models import Users
from fastapi import Depends, APIRouter
from app.schemas.stats import *
from app.core.JWT.auth import require_role, get_current_user
import logging

logger = logging.getLogger(__name__)
stats_router = APIRouter(
    prefix= '/stats',
    tags= ['statistics']
)

@stats_router.get('/my_stats', response_model= AnswersStats)
async def get_answer_my_stats(session: AsyncSession = Depends(get_async_session),
                              current_user: Users = Depends(get_current_user)):
    return await StatService.my_stat(session = session,
                                     current_user = current_user)


@stats_router.get('/admin/overview', response_model=Stats_User)
async def get_stats_user(session: AsyncSession = Depends(get_async_session),
                         current_user: Users = Depends(require_role('Админ'))):
    return await StatService.overview(session = session,
                                      current_user = current_user)


@stats_router.get('/questions/{question_id}/answers', response_model= list[AnswerDetail])
async def get_answers(question_id: int,
                      session: AsyncSession = Depends(get_async_session),
                      current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    return await StatService.answers_stats(session = session,
                                           current_user = current_user,
                                           question_id = question_id)
