import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from Database.models import Base
from httpx import AsyncClient, ASGITransport
from API.main import app
from Database.database import get_async_session
from config_app import generate_url_db

url = generate_url_db() + '_Test'
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
    async with AsyncSession(test_engine) as session:
        # Начинаем транзакцию без контекстного менеджера
        await session.begin()
        yield session
        # Откатываем изменения после теста
        await session.rollback()


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