from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl, validator
from typing import Optional, List, Literal, Union


class Ban_Base(BaseModel):
    reason: str

class Ban_Create(Ban_Base):
    expires_at: datetime | None

class Ban_Read(Ban_Base):
    created_at: datetime

    class Config:
        from_attributes = True