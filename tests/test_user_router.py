import pytest
import pytest_asyncio

from Database.models import Users
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

@pytest.mark.parametrize('telegram_id, username, role, is_banned',
                         [(0, 'Olef', 'Ученик', False),
                          (1, 'Ivan', 'Преподаватель', False),
                          (2, 'Igor', 'Админ', False)])
async def test_create_user(telegram_id, username, role, is_banned, client):
    response = await client.post('/users/create', json= {'telegram_id': telegram_id, 'username': username, 'role': role, 'is_banned': is_banned})

    assert response.status_code == 201
    data = response.json()
    assert data['telegram_id'] == telegram_id
    assert data['username'] == username
    assert data['role'] == role
    assert data['is_banned'] == is_banned


@pytest_asyncio.fixture
async def auth_token(client):
    data = {'telegram_id': 1, 'username': 'Ivan', 'role': 'Преподаватель', 'is_banned': False}
    response = await client.post('/users/create', json = data)
    telegram_id = response.json()['telegram_id']

    token_response = await client.post('/auth/login', json= {'telegram_id': telegram_id})
    token = token_response.json()['access_token']
    print(token_response.status_code)
    print(token_response.json())
    return token
async def test_get_user_info(auth_token, client):
    response = await client.get('/users/me',
                           headers={'Authorization': f"Bearer {auth_token}"})
    assert response.status_code == 200
