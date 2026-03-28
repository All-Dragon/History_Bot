import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

async def test_login_token(client, mocker):
    await client.post('/users/create', json={
        'telegram_id': 777, 'username': 'Test', 'role': 'Ученик', 'is_banned': False
    })

    mock_token = mocker.patch("services.auth_service.create_access_token")
    mock_token.return_value = 'fake'

    response = await client.post('/auth/login', json = {'telegram_id': 777})
    assert response.status_code == 200
    assert response.json().get('access_token') == 'fake'

async def test_error_login_token(client, mocker):
    await client.post('/users/create', json={
        'telegram_id': 777, 'username': 'Test', 'role': 'Ученик', 'is_banned': False
    })

    mock_token = mocker.patch('services.auth_service.create_access_token')
    mock_token.side_effect = Exception("Ошибка генерации токена")

    response = await client.post('/auth/login', json = {'telegram_id': 777})
    assert response.status_code != 200
