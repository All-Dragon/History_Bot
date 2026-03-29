# 📚 History Bot

Сервис для управления образовательными тестами и вопросами через Telegram бот с REST API.

## 🎯 Возможности

- **Telegram Bot** — интерфейс для учеников и учителей
- **REST API** — полнофункциональное API для интеграций
- **Система аутентификации** — JWT-токены с ролевым доступом
- **Управление вопросами** — создание, редактирование, категоризация вопросов
- **Система тестирования** — проведение тестов, отслеживание результатов
- **Статистика** — аналитика по пользователям и результатам
- **Система банов** — управление доступом пользователей
- **Асинхронная БД** — PostgreSQL с asyncpg для высокой производительности

---

## 📋 Требования

- **Python** 3.10+
- **PostgreSQL** 12+
- **Redis** (опционально)
- **Docker & Docker Compose** (для контейнеризации)

---
## 🛠 Стек проекта

- Python 3.10+
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL
- Alembic
- Aiogram
- Docker
- Redis
- Pytest
---
## 🚀 Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/All-Dragon/History_Bot.git
cd HistoryBot
```

### 2. Создание виртуального окружения
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Конфигурация переменных окружения
Создайте файл `.env` в корне проекта:

```env
# Database Configuration
DB_NAME = DB_Name
DB_HOST = DB_HOST
DB_USER = DB_USERNAME
DB_PASSWORD = YOUR_DB_PASSWORD
DB_PORT = DB_PORT

# Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN
ADMIN_IDS= YOUR_ADMIN_LIST

# Redis Configuration
REDIS_DATABASE=1
REDIS_HOST=YOUR_REDIS_HOST
REDIS_PORT=YOUR_REDIS_PORT
REDIS_USERNAME=YOUR_REDIS_USERNAME
REDIS_PASSWORD=YOUR_REDIS_PASSWORD

# API Configuration
API_BASE_URL = API_BASE_URL

# JWT Configuration
SECRET_KEY=your_super_secret_key_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Создайте файл `.env.docker` в корне проекта:
```
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=your_admin_ids

# Database Configuration
DB_NAME=your_db_name
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db:5432/your_db_name

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DATABASE=0
REDIS_USERNAME=default
REDIS_PASSWORD=your_redis_password

# API Configuration
API_BASE_URL=http://app:8000

# JWT Configuration
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📦 Структура проекта

```
HistoryBot/
├── API/                    # REST API (FastAPI)
│   ├── main.py
│   └── routers/           # Маршруты по сущностям
│       ├── auth.py
│       ├── users_router/
│       ├── questions_router/
│       ├── answers_router/
│       ├── stats_router/
│       ├── bans_router/
│       └── tests_router/
│
├── Bot/                    # Telegram Bot (Aiogram)
│   ├── main.py
│   ├── handlers/          # Обработчики команд
│   │   ├── authentication_handlers/
│   │   ├── teacher_handlers/
│   │   ├── get_questions_handler.py
│   │   └── stats_handler.py
│   └── utils/            # Вспомогательные функции
│       ├── auth_check.py
│       └──keyboards.py
│       
│
├── Database/              # Слой базы данных
│   ├── database.py        # Подключение и сессии
│   └── models.py          # SQLAlchemy модели
│
├── JWT/                   # Аутентификация и безопасность
│   ├── auth.py
│   ├── security.py
│   └── token_shemas.py
│
├── alembic/              # Миграции базы данных
│   ├── env.py
│   ├── versions/
│   └── script.py.mako
│
├── tests/                # Модульные и интеграционные тесты
│   ├── conftest.py
│   ├── test_questions_router.py
│   ├── test_user_router.py
│   └── test_answer_router.py
│
├── config_app.py         # Конфигурация приложения
├── docker-compose.yaml   # Docker Compose конфиг
├── Dockerfile            # Docker образ
├── alembic.ini          # Alembic конфиг для миграций
├── pytest.ini           # Pytest конфиг
├── requirements.txt     # Зависимости Python
└── README.md           # Этот файл
```

---

## ▶️ Запуск

### Локально

#### 1. Подготовьте базу данных
```bash
# Убедитесь, что PostgreSQL запущен и БД создана
```

#### 2. Примените миграции
```bash
alembic upgrade head
```

#### 3. Запустите API сервер
```bash
cd api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступен по адресу: `http://localhost:8000`

#### 4. В другом терминале запустите Telegram Bot
```bash
cd Bot
python main.py
```

### Docker Compose

```bash
docker-compose up -d
```

Сервисы:
- **API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## 📖 API Документация

После запуска API откройте в браузере:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

### Основные эндпоинты

| Метод | Маршрут | Описание |
|-------|---------|---------|
| GET | `/health` | Проверка статуса сервера |
| POST | `/auth/login` | Аутентификация пользователя |
| GET | `/question` | Получить все вопросы |
| POST | `/question` | Создать вопрос (только учителя) |
| GET | `/stats/my_stats` | Получить личную статистику |
| GET | `/stats/admin/overview` | Статистика админа |
| POST | `/bans` | Забанить пользователя |

---

## 🧪 Тестирование

Запустите тесты:
```bash
pytest
```

С подробным выводом:
```bash
pytest -v
```

С покрытием:
```bash
pytest --cov=api --cov=Bot
```

---

## 🔐 Аутентификация

Проект использует **JWT (JSON Web Tokens)** для аутентификации:

1. Пользователь отправляет учетные данные
2. Сервер возвращает JWT токен
3. Токен включается в заголовок `Authorization: Bearer <token>`
4. Сервер проверяет токен для защищенных маршрутов

### Роли

- **Админ** — полный доступ ко всем функциям
- **Преподаватель** — создание и управление вопросами
- **Ученик** — прохождение тестов и просмотр результатов

---

## 📦 Требования к БД

### PostgreSQL расширения
```sql
-- Убедитесь, что установлены:
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Автоматические зависимости
При установке основных пакетов из `requirements.txt` также установятся:
- `aiofiles`, `certifi`, `cryptography` — для безопасности и файлов
- `httpx`, `httpcore` — для HTTP запросов
- `Mako`, `MarkupSafe` — для Alembic шаблонов
- и другие служебные пакеты

---

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|---------|-------------|
| `BOT_TOKEN` | Токен Telegram бота | *(обязательно)* |
| `ADMIN_IDS` | ID админов через запятую | [] |
| `DB_NAME` | Имя БД | - |
| `DB_HOST` | Хост БД | localhost |
| `DB_PORT` | Порт БД | 5432 |
| `DB_USER` | Пользователь БД | - |
| `DB_PASSWORD` | Пароль БД | - |
| `REDIS_HOST` | Хост Redis | localhost |
| `REDIS_PORT` | Порт Redis | 6379 |
| `SECRET_KEY` | Секретный ключ JWT | *(обязательно)* |
| `ALGORITHM` | Алгоритм JWT | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена | 30 |
| `API_BASE_URL` | URL API сервера | http://localhost:8000 |

---

## 🐛 Решение проблем

### Ошибка подключения к БД
```
ensure you have set the correct password and are using the correct host
```
**Решение**: Проверьте переменные окружения в `.env`

### Telegram бот не отвечает
```
Socket hang up
```
**Решение**: Убедитесь, что `BOT_TOKEN` правильный и интернет подключен

### Миграции не применяются
```
FAILED: Can't locate revision identified by 'abc123'
```
**Решение**: Используйте `alembic current` для проверки текущей версии

---

## 📝 Лицензия

MIT License - см. LICENSE файл

---

## 👥 Контрибьютинг

1. Fork репозиторий
2. Создайте branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

---

## 📧 Поддержка

По вопросам и предложениям пишите в Issues или на почту.

---
