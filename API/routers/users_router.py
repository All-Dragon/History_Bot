from API.schemas import *
from Database.database import get_async_session
from Database.models import *


users_router = APIRouter(
    prefix= '/users',
    tags= ['users']
)

@users_router.get('')
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.scalars(select(Users))
    result = result.all()
    return result

@users_router.post('/create', response_model= ReadeUser, status_code= status.HTTP_201_CREATED)
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
    return new_user

@users_router.put('/change/{telegram_id}', response_model= ReadeUser)
async def change(id: int, data: Change_User, session: AsyncSession = Depends(get_async_session)):

    user = await session.scalar(select(Users).where(Users.telegram_id == id))
    if user is None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= 'Пользователь с таким id не найден')

    updated_data = data.model_dump(exclude_unset=True, exclude_none= True)

    for field, value in updated_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user

