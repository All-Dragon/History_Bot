import logging
import os
from dataclasses import dataclass
from urllib.parse import quote
from environs import Env

@dataclass
class JWTSettings:
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

@dataclass
class APISettings:
    base_url: str

@dataclass
class BotSettings:
    token: str
    admin_ids: list[int]


@dataclass
class DatabaseSettings:
    name: str
    host: str
    port: int
    user: str
    password: str


@dataclass
class RedisSettings:
    host: str
    port: int
    db: int
    password: str
    username: str


@dataclass
class Config:
    bot: BotSettings
    db: DatabaseSettings
    redis: RedisSettings
    api: APISettings
    jwt: JWTSettings


def load_config(path: str | None = None) -> Config:

    env = Env()

    env.read_env(path)

    token = env("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN must not be empty")

    raw_ids = env.list("ADMIN_IDS", default=[])

    try:
        admin_ids = [int(x) for x in raw_ids]
    except ValueError as e:
        raise ValueError(f"ADMIN_IDS must be integers, got: {raw_ids}") from e

    db = DatabaseSettings(
        name=env("DB_NAME"),
        host=env("DB_HOST"),
        port=env.int("DB_PORT"),
        user=env("DB_USER"),
        password=env("DB_PASSWORD"),
    )

    redis = RedisSettings(
        host=env("REDIS_HOST"),
        port=env.int("REDIS_PORT"),
        db=env.int("REDIS_DATABASE"),
        password=env("REDIS_PASSWORD", default=""),
        username=env("REDIS_USERNAME", default=""),
    )

    api = APISettings(
        base_url= os.getenv('API_BASE_URL', 'http://localhost:8000')
    )

    jwt = JWTSettings(
        SECRET_KEY= os.getenv('SECRET_KEY'),
        ALGORITHM = os.getenv('ALGORITHM'),
        ACCESS_TOKEN_EXPIRE_MINUTES= os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
    )


    return Config(
        bot=BotSettings(token=token, admin_ids=admin_ids),
        db=db,
        redis=redis,
        api = api,
        jwt = jwt
    )

def generate_url_db():
    config: Config = load_config()
    url = f'postgresql+asyncpg://{quote(config.db.user, safe='')}:{quote(config.db.password, safe = '')}@{config.db.host}:{config.db.port}/{config.db.name}'
    return url

if __name__ == "__main__":
    config = load_config()
    print(config.jwt.ALGORITHM)


