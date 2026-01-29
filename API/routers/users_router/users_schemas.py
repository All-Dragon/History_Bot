from datetime import datetime, date, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl, validator
from typing import Optional, List, Literal, Union


class UsersBase(BaseModel):
    telegram_id: int = Field(..., description= 'User telegram id')
    username: Optional[str] = Field(default= None, min_length=1, max_length=255, description="User's full name")

    @field_validator('username')
    @classmethod
    def validation_username(cls, name: str | None):
        if name is not None:
            if not name or len(name.strip()) == 0:
                raise ValueError('Name cannot be empty')
            return name.strip()
        return None

class CreateUser(UsersBase):
    role: str = Field(..., examples= ['Ученик'])
    is_banned: bool = Field(default= False, description= 'User is banned or not')

class ReadUser(UsersBase):
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default= None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(default= None, description= 'Active user or not')

    @field_validator('updated_at')
    @classmethod
    def check_updated_at(cls, v: datetime | None):
        if v:
            return v
        return None

    class Config:
        from_attributes = True

class Change_User(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=255, description="User's full name")
    role: Optional[str] = None
    is_banned: Optional[bool] = None


    @field_validator('username')
    @classmethod
    def validation_username(cls, name: str | None):
        if name is not None:
            if not name or len(name.strip()) == 0:
                raise ValueError('Name cannot be empty')
            return name.strip()
        return None

class User_Out(BaseModel):
    id: int
    telegram_id: int
    username: str
    role: str
    is_banned: bool

    model_config = {"from_attributes": True}

class ChangeName(BaseModel):
    name: str
