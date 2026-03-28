import logging

import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from API.main import app
from Database.database import get_async_session
from Database.models import Base
from config_app import generate_url_db
from httpx import ASGITransport, AsyncClient

for logger_name in ["API", "Bot", "uvicorn", "uvicorn.access", "uvicorn.error"]:
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

url = generate_url_db() + "_Test"
test_engine = create_async_engine(url, poolclass=NullPool)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    # Создаём таблицы перед всеми тестами
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Удаляем таблицы после всех тестов
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        await session.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(sync_session, transaction_):
            parent = getattr(transaction_, "_parent", None)
            if transaction_.nested and (parent is None or not parent.nested):
                sync_session.expire_all()
                if not connection.sync_connection.in_nested_transaction():
                    connection.sync_connection.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            if transaction.is_active:
                await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    # Переопределяем зависимость get_async_session для тестов
    async def override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client

    # Очищаем переопределение после теста
    app.dependency_overrides.clear()