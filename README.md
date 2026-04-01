# History Bot

History Bot — это backend-проект с Telegram-ботом и REST API для работы с пользователями, вопросами, ответами, статистикой и банами.

Проект состоит из двух основных частей:

- `FastAPI` API, через которое работает бизнес-логика и база данных
- `Aiogram`-бот, который использует это API как клиент

## Быстрый старт

Если нужен самый короткий путь до первого запуска:

1. Скопировать `.env.example` в `.env`
2. Заполнить `BOT_TOKEN`, `DB_*`, `SECRET_KEY`
3. Поднять PostgreSQL и Redis
4. Выполнить `alembic upgrade head`
5. Запустить API: `uvicorn app.api.main:app --reload`
6. Запустить бота: `python -m app.Bot.main`

## Что умеет проект

### API

- регистрация пользователей и вход по `telegram_id`
- выдача JWT-токена
- просмотр своего профиля и смена имени
- создание и просмотр вопросов
- выдача случайного опубликованного вопроса
- отправка ответов
- просмотр личной статистики
- админская статистика по пользователям
- бан и разбан пользователей
- soft delete / restore пользователя

### Telegram-бот

- регистрация
- логин
- просмотр профиля
- смена имени
- получение случайного вопроса
- получение вопроса по ID
- просмотр личной статистики
- админская статистика
- создание вопросов преподавателем через пошаговый сценарий
- просмотр своих вопросов
- просмотр ответов на свой вопрос

## Технологии

- Python 3.12
- FastAPI
- Aiogram 3
- SQLAlchemy 2.0 Async
- PostgreSQL
- Alembic
- HTTPX
- Aiohttp
- Pytest + pytest-asyncio + pytest-mock
- Docker / Docker Compose

## Архитектура

Сейчас проект организован как монолит с разделением по слоям:

- `app/api` — HTTP-роуты FastAPI
- `app/services` — бизнес-логика
- `app/repositories` — доступ к данным
- `app/db` — подключение к БД и ORM-модели
- `app/schemas` — Pydantic-схемы
- `app/core` — конфиг, JWT, логирование
- `app/Bot` — Telegram-бот
- `tests` — тесты API

Схема взаимодействия:

```text
Telegram user
    ↓
Aiogram bot
    ↓ HTTP
FastAPI API
    ↓
Services
    ↓
Repositories
    ↓
PostgreSQL
```

## Структура проекта

```text
HistoryBot/
├── app/
│   ├── api/
│   │   ├── main.py
│   │   └── routers/
│   │       ├── answers.py
│   │       ├── auth.py
│   │       ├── bans.py
│   │       ├── questions.py
│   │       ├── stats.py
│   │       └── users.py
│   ├── Bot/
│   │   ├── main.py
│   │   ├── handlers/
│   │   │   ├── authentication_handlers/
│   │   │   ├── teacher_handlers/
│   │   │   ├── get_questions_handler.py
│   │   │   └── stats_handler.py
│   │   └── utils/
│   ├── core/
│   │   ├── config_app.py
│   │   ├── logging_config.py
│   │   └── JWT/
│   ├── db/
│   │   ├── database.py
│   │   └── models/
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── alembic/
├── tests/
├── .env.example
├── .env.docker.example
├── docker-compose.yaml
├── Dockerfile
├── alembic.ini
├── pytest.ini
└── requirements.txt
```

## Переменные окружения

Проект использует `.env` для локального запуска и `.env.docker` для контейнеров.

Важно:

- `ADMIN_IDS` ожидается как список чисел через запятую, например `123456789,987654321`
- сейчас конфигурация читается централизованно, поэтому без `BOT_TOKEN` приложение тоже не стартует, даже если вы хотите поднять только API
- подготовьте `.env` и `.env.docker` до запуска сервисов, чтобы все работало исправно
### Как подготовить `.env` 

Скопируйте пример:

```bash
copy .env.example .env
```

или на Unix/macOS:

```bash
cp .env.example .env
```

Актуальные переменные из `.env.example`:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=your_admin_ids

DB_NAME=your_db_name
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DATABASE=0
REDIS_USERNAME=default
REDIS_PASSWORD=default

API_BASE_URL=http://localhost:8000

SECRET_KEY=your_super_secret_key_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Как подготовить `.env.docker`

Скопируйте пример:

```bash
copy .env.docker.example .env.docker
```

или:

```bash
cp .env.docker.example .env.docker
```

Актуальные переменные из `.env.docker.example`:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=your_admin_ids

DB_NAME=your_db_name
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db:5432/your_db_name

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DATABASE=0
REDIS_USERNAME=default
REDIS_PASSWORD=your_redis_password

API_BASE_URL=http://app:8000

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Локальный запуск

### 1. Установить зависимости

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Поднять PostgreSQL и Redis

Нужны:

- PostgreSQL
- Redis

Можно использовать локально установленные сервисы или контейнеры.

### 3. Применить миграции

```bash
alembic upgrade head
```

### 4. Запустить API

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

После запуска API будет доступно по адресам:

- `http://localhost:8000`
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`
- `http://localhost:8000/health`

### 5. Запустить Telegram-бота

В отдельном терминале:

```bash
python -m app.Bot.main
```

## Docker

В репозитории есть `Dockerfile` и `docker-compose.yaml`, для запуска сборки использовать команду ниже:

```bash
docker compose up --build
```

Обязательно должен быть заполнен файл:`.env.docker`

## API-роуты

### Auth

- `POST /auth/login` — получить JWT по `telegram_id`

### Users

- `GET /users` — получить список пользователей, только админ
- `GET /users/me` — получить свой профиль
- `POST /users/create` — создать пользователя
- `PUT /users/me/name` — изменить свое имя
- `PUT /users/change/{telegram_id}` — изменить пользователя, только админ
- `DELETE /users/hard_del/{telegram_id}` — удалить пользователя, только админ
- `DELETE /users/soft_del` — soft delete текущего пользователя
- `PUT /users/restore_user` — восстановить текущего пользователя
- `GET /users/{telegram_id}` — получить пользователя по `telegram_id`

### Questions

- `GET /question` — все вопросы, преподаватель или админ
- `GET /question/my` — свои вопросы, преподаватель или админ
- `GET /question/random` — случайный опубликованный вопрос
- `GET /question/{question_id}` — вопрос по ID
- `POST /question/new` — создать вопрос, преподаватель или админ

### Answers

- `GET /answers` — все ответы, только админ
- `POST /answers/create` — отправить ответ
- `GET /answers/{answer_id}` — получить ответ по ID, только админ

### Bans

- `GET /bans` — список банов, только админ
- `GET /bans/{telegram_id}` — информация о бане, только админ
- `POST /bans` — забанить пользователя, только админ
- `DELETE /bans/{telegram_id}` — разбанить пользователя, только админ

### Stats

- `GET /stats/my_stats` — личная статистика
- `GET /stats/admin/overview` — статистика по пользователям, только админ
- `GET /stats/questions/{question_id}/answers` — ответы на вопрос, преподаватель или админ

## Команды Telegram-бота

### Общие

- `/start` - начало работы с ботом
- `/help` - получение помощи по командам
- `/registration` - регистрация
- `/login` - вход в систему
- `/profile` - просмотр своего профиля
- `/change_name` - смена имени пользователя
- `/random` - случайный вопрос
- `/question <id>` - получение вопроса по его id
- `/my_stats` - статистика пользователя

### Для преподавателя

- `/add_question` - добавить вопрос
- `/my_questions` - созданные пользователем вопросы
- `/result <question_id>` - просмотр ответов на вопрос question_id

### Для администратора

- `/users_states` - статистика по использованию сервиса

## Роли

В проекте используются три роли:

- `Ученик`
- `Преподаватель`
- `Админ`

Роли проверяются в API через JWT-зависимости, а в боте — через запросы к API.

## Тесты

Тесты находятся в папке `tests/`.

Запуск:

```bash
pytest
```

Или подробнее:

```bash
pytest -v
```

Особенности:

- тесты используют отдельную тестовую БД с суффиксом `_Test`
- `tests/conftest.py` переопределяет зависимость `get_async_session`
- для изоляции тестов используется внешняя транзакция и nested transaction/savepoint

## Миграции

Для управления схемой используется Alembic.

Основные команды:

```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "message"
```

Файл конфигурации Alembic: `alembic/env.py`

## Полезные файлы

- `app/api/main.py` — точка входа FastAPI
- `app/Bot/main.py` — точка входа Telegram-бота
- `app/core/config_app.py` — загрузка конфигурации
- `app/db/database.py` — подключение к БД
- `app/db/models/__init__.py` — экспорт моделей
- `tests/conftest.py` — тестовая инфраструктура


