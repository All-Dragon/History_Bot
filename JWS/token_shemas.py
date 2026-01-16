from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl, validator
from typing import Optional, List, Literal, Union

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class Token_Data(BaseModel):
    telegram_id: int
    role: str

class Telegram_Login(BaseModel):
    telegram_id: int