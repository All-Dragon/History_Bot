from fastapi import FastAPI
from API.routers.users_router.users_router import users_router
from API.routers.questions_router.questions_router import questions_router
from API.routers.bans_router.bans_router import bans_router


app = FastAPI(title= "API History_Bot", description= 'Это API для работы с History_Bot')

@app.get('/')
async def main_menu():
    return {'API menu':
                {'project': '/project',
                 'employee': "/employee",
                'Документация': '/docx'}}

app.include_router(users_router)
app.include_router(questions_router)
app.include_router(bans_router)