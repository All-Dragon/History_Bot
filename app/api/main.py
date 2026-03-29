import logging

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routers.answers import answers_router
from app.api.routers.auth import authorization_router
from app.api.routers.bans import bans_router
from app.api.routers.questions import questions_router
from app.api.routers.stats import stats_router
from app.api.routers.users import users_router
from app.core.logging_config import setup_logging
setup_logging()

APP_VERSION = "1.0.0"
SERVICE_NAME = "History Bot api"


app = FastAPI(title= SERVICE_NAME, version= APP_VERSION, description= 'Это api для работы с History_Bot')
logger = logging.getLogger(__name__)

@app.get("/health", include_in_schema=False)
async def health():
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": APP_VERSION
    }


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def main_menu():
    return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>{SERVICE_NAME}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f5f7fa;
                    padding: 40px;
                }}
                .card {{
                    max-width: 600px;
                    margin: auto;
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
                }}
                .meta {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                a {{
                    display: block;
                    margin: 10px 0;
                    text-decoration: none;
                    color: #2563eb;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>📚 {SERVICE_NAME}</h1>
                <div class="meta">
                    Версия: <strong>{APP_VERSION}</strong><br>
                    Статус: <span style="color: green;">● online</span>
                </div>

                <p>api для работы с History Bot</p>

                <h3>Навигация</h3>
                <a href="/docs">📘 Swagger UI</a>
                <a href="/redoc">📕 ReDoc</a>
                <a href="/health">🩺 Health check</a>
            </div>
        </body>
        </html>
        """

app.include_router(authorization_router)
app.include_router(users_router)
app.include_router(questions_router)
app.include_router(answers_router)
app.include_router(bans_router)
app.include_router(stats_router)
