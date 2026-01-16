from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from JWS.security import decode_token
from Database.database import get_async_session
from Database.models import Users
from JWS.token_shemas import Token_Data

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login') # Путь к эндпоинту

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_async_session)
):
    token_data = Token_Data(**decode_token(token))

    if token_data.telegram_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await session.scalar(
        select(Users).where(Users.telegram_id == token_data.telegram_id)
    )

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned")

    return user

def require_role(*roles: str):
    async def checker(current_user: Users = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(403, f"Требуется роль: {', '.join(roles)}")
        return current_user
    return checker
