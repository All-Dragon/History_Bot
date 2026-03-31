import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Твои импорты (подставь правильные пути)
from app.db.models import Base           # ← твои модели
from app.core.config_app import generate_url_db     # или from config import settings


# Alembic Config объект
config = context.config

# Устанавливаем URL (лучше один раз здесь, чем дублировать в offline/online)
try:
    db_url = generate_url_db()              # или settings.DATABASE_URL
    config.set_main_option("sqlalchemy.url", db_url)
except Exception as e:
    raise RuntimeError(f"Не удалось получить URL базы данных:\n{e}")


# Логирование из alembic.ini (если нужно)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Метаданные моделей для автогенерации миграций
target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    """Синхронная функция, которая выполняет сами миграции"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Offline-режим (генерация SQL в консоль без подключения)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Online-режим с асинхронным движком"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Самое важное место — выполняем синхронную логику миграций в потокобезопасном режиме
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# Запуск в зависимости от режима
if context.is_offline_mode():
    run_migrations_offline()
else:
    # Запускаем асинхронную функцию
    asyncio.run(run_migrations_online())