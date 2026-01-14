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
from pydantic import BaseModel, Field
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
from API.schemas import *
from Database.database import get_async_session
from Database.models import *
from API.routers.users_router import users_router

app = FastAPI(title= "API History_Bot", description= 'Это API для работы с History_Bot')

@app.get('/')
async def main_menu():
    return {'API menu':
                {'project': '/project',
                 'employee': "/employee",
                'Документация': '/docx'}}

app.include_router(users_router)
