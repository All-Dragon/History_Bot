from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config_app import Config, load_config, generate_url_db

config: Config = load_config()
url = generate_url_db()
engine = create_async_engine(url)
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit= False,
    class_ = AsyncSession
)

async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


