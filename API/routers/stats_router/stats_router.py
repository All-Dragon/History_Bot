from API.routers.bans_router.bans_schemas import *
from Database.database import get_async_session, AsyncSession
from Database.models import *
from fastapi import Depends, status, HTTPException, APIRouter
from API.routers.stats_router.stats_schemas import *
from JWT.auth import require_role, get_current_user

stats_router = APIRouter(
    prefix= '/stats',
    tags= ['statistics']
)

@stats_router.get('/my_stats', response_model= AnswersStats)
async def get_answer_my_stats(session: AsyncSession = Depends(get_async_session),
                              current_user: Users = Depends(get_current_user)):

    try:
        result = await session.execute(
            select(
                func.sum(
                    case(
                        (Answers.user_id == current_user.id, 1),
                        else_= 0
                    )
                ).label('total_question'),

                func.sum(
                    case(
                        (
                            (Answers.user_id  == current_user.id) &
                            (Answers.is_correct == True),
                            1
                        ),

                        else_= 0
                    )
                ).label('right_answer')

            )
        )

        stats_row = result.one()
        stats_data = {
            'total_question': stats_row.total_question,
            'right_answer': stats_row.right_answer
        }

        return AnswersStats(**stats_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics"
        )


@stats_router.get('/admin/overview', response_model=Stats_User)
async def get_stats_user(session: AsyncSession = Depends(get_async_session),
                         current_user: Users = Depends(require_role('Админ'))):
    try:
        result = await session.execute(
            select(
                func.count(Users.id).label('total_user'),

                func.count(
                    case(
                        (Users.deleted_at.is_(None), Users.id)
                    )
                ).label('current_user'),

                func.count(
                    case(
                        (Users.deleted_at.isnot(None), Users.id)
                    )
                ).label('deleted_user')
            )
        )
        stats_row = result.one()
        stats_data = {
            'total_user': stats_row.total_user,
            'current_user': stats_row.current_user,
            'deleted_user': stats_row.deleted_user
        }
        return Stats_User(**stats_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics"
        )