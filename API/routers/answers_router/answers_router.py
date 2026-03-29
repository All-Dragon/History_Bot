from API.routers.bans_router.bans_schemas import *
from services.answer_service import AnswerService
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from API.routers.answers_router.answer_schemas import *
from JWT.auth import require_role, get_current_user
import logging

logger = logging.getLogger(__name__)
answers_router = APIRouter(
    prefix= '/answers',
    tags= ['answers']
)

@answers_router.get('')
async def get_all_answers(session: AsyncSession = Depends(get_async_session),
                          current_user: Users = Depends(require_role('Админ'))):
    return await AnswerService.all(session = session,
                                   current_user = current_user)

@answers_router.post('/create', response_model= AnswerRead, status_code= status.HTTP_201_CREATED)
async def create_answer(data: AnswerCreate,
                        current_user: Users = Depends(get_current_user),
                        session: AsyncSession = Depends(get_async_session)
                        ):
    new_answer = await AnswerService.create(session = session,
                                            current_user = current_user,
                                            data = data)
    return AnswerRead.model_validate(new_answer)


@answers_router.get('/{answer_id}', response_model= AnswerRead)
async def get_answer_by_id(answer_id: int,
                           session: AsyncSession = Depends(get_async_session),
                           current_user: Users = Depends(require_role('Админ'))):
    answer = await AnswerService.get(session = session,
                                     answer_id = answer_id,
                                     current_user = current_user)
    return AnswerRead.model_validate(answer)

