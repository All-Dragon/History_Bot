from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from JWT.security import decode_token
from Database.database import get_async_session
from Database.models import Users
from JWT.token_shemas import Token_Data

security = HTTPBearer()  # Вместо OAuth2PasswordBearer

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        session: AsyncSession = Depends(get_async_session)
):
    """
    Получить текущего пользователя по JWT токену.
    Проверяет валидность токена и статус бана.
    """
    token = credentials.credentials
    try:
        token_data = Token_Data(**decode_token(token))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if token_data.telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = await session.scalar(
        select(Users).where(Users.telegram_id == token_data.telegram_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned"
        )

    return user

def require_role(*roles: str):
    """
    Зависимость для проверки ролей пользователя.
    
    Пример использования:
        @router.post('/create')
        async def create(current_user: Users = Depends(require_role('Преподаватель', 'Модератор'))):
            ...
    """
    async def checker(current_user: Users = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}"
            )
        return current_user
    return checker
