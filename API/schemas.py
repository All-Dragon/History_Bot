from dotenv import load_dotenv
import logging
import os
from aiogram import Dispatcher, Bot, types, F, BaseMiddleware
from aiogram.filters import CommandStart, Command, BaseFilter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (InlineKeyboardMarkup,InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, ReplyKeyboardRemove,
                           KeyboardButtonPollType, BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, TelegramObject, User, InputMediaAudio,
                           InputMediaDocument, InputMediaPhoto,
                           InputMediaVideo, PhotoSize)
from aiogram.enums import PollType
import asyncio
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup, KeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import create_engine, String, Integer, ForeignKey, text, Boolean, select, or_, desc, asc, func, Table, \
    Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship, selectinload, joinedload, \
    sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from pydantic import BaseModel, Field, field_validator
import random
from aiogram.exceptions import  TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
import datetime
import re
from aiogram import Router
from aiogram.client.bot import Bot
from aiogram.filters.callback_data import CallbackData
from typing import Any, Awaitable, Callable
import aiohttp
from datetime import datetime, date

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
    role: str
    is_banned: bool = Field(default= False, description= 'User is banned or not')

class ReadeUser(UsersBase):
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default= None, description="Last update timestamp")

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
