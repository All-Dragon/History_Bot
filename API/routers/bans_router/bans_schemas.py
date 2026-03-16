from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl, validator
from typing import Optional, List, Literal, Union


class Ban_Base(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for ban")

class Ban_Create(Ban_Base):
    telegram_id: int = Field(..., description="User telegram ID to ban")
    expires_at: Optional[datetime] = Field(None, description="Ban expiration time (None for permanent)")

class Ban_Read(Ban_Base):
    id: int = Field(..., description="Ban ID")
    user_id: int = Field(..., description="Banned user ID")
    created_at: datetime = Field(..., description="Ban creation time")
    expires_at: Optional[datetime] = Field(None, description="Ban expiration time")

    class Config:
        from_attributes = True

class Ban_Info(BaseModel):
    telegram_id: int = Field(..., description="User telegram ID")
    reason: str = Field(..., description="Reason for ban")
    is_banned: bool = Field(..., description="User ban status")
    expires_at: Optional[datetime] = Field(None, description="Ban expiration time")
    
    class Config:
        from_attributes = True