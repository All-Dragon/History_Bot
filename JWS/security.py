from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from fastapi import HTTPException, status
from config_app import load_config, Config

config: Config = load_config()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire =  datetime.now(timezone.utc) + timedelta(minutes= 15)

    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt.SECRET_KEY, algorithm= config.jwt.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, config.jwt.SECRET_KEY, algorithms= [config.jwt.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )