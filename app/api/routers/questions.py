from app.schemas.questions import *
from app.Database.database import get_async_session, AsyncSession
from app.Database.models import *
from fastapi import Depends, status, APIRouter
from typing import List
from app.core.JWT.auth import require_role
from app.services.questions import QuestionService
import logging

logger = logging.getLogger(__name__)

questions_router = APIRouter(
    prefix= '/question',
    tags = ['question']
)


@questions_router.get('', response_model=List[QuestionOut])
async def get_all_questions(session: AsyncSession = Depends(get_async_session),
                            current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    return await QuestionService.all(session = session, current_user = current_user)

@questions_router.get('/my', response_model= List[QuestionOut])
async def get_my_questions(session: AsyncSession = Depends(get_async_session),
                           current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    return await QuestionService.all_my(session = session, current_user = current_user)


@questions_router.get("/random", response_model=QuestionOut)
async def get_random_question(
    session: AsyncSession = Depends(get_async_session),
    topic: Optional[str] = None,
    difficulty: Optional[int] = None
):
    question = await QuestionService.random(session = session,
                                            topic = topic,
                                            difficulty = difficulty)
    return QuestionOut.model_validate(question)


@questions_router.get('/{question_id}', response_model= QuestionOut)
async def get_question_by_id(question_id: int, session: AsyncSession = Depends(get_async_session)):
    question = await QuestionService.by_id(session = session,
                                           question_id = question_id)
    return QuestionOut.model_validate(question)


@questions_router.post('/new', status_code= status.HTTP_201_CREATED, response_model= QuestionOut)
async def create_question(
        data: QuestionCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: Users = Depends(require_role('Преподаватель', 'Админ'))):
    question = await QuestionService.create(session = session,
                                            data = data,
                                            current_user = current_user)
    return QuestionOut.model_validate(question)
