import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone


@pytest_asyncio.fixture
async def admin_token(client):
    import random
    telegram_id = random.randint(10000, 99999)

    data = {'telegram_id': telegram_id, 'username': 'Admin', 'role': 'Админ', 'is_banned': False}
    response = await client.post('/users/create', json=data)

    token_response = await client.post('/auth/login', json={'telegram_id': telegram_id})
    token = token_response.json()['access_token']
    return token


@pytest_asyncio.fixture
async def regular_user(client):
    import random
    telegram_id = random.randint(10000, 99999)

    data = {'telegram_id': telegram_id, 'username': 'Regular', 'role': 'Ученик', 'is_banned': False}
    response = await client.post('/users/create', json=data)

    token_response = await client.post('/auth/login', json={'telegram_id': telegram_id})
    token = token_response.json()['access_token']
    return {'telegram_id': telegram_id, 'token': token}


@pytest.mark.parametrize('telegram_id, username, role, is_banned, reason, expires_at', [
    (100, 'User01', 'Преподаватель', False, 'Spam', None),
    (101, 'User02', 'Преподаватель', False, 'Cheating', None),
    (102, 'User03', 'Преподаватель', False, 'Temporary ban', datetime.now(timezone.utc) + timedelta(days=7))
])
async def test_create_ban(client, admin_token, telegram_id, username, role, is_banned, reason, expires_at):
    response_create = await client.post('/users/create', 
                                        json={'telegram_id': telegram_id, 
                                              'username': username, 
                                              'role': role, 
                                              'is_banned': is_banned})
    assert response_create.status_code == 201

    ban_data = {
        'telegram_id': telegram_id,
        'reason': reason,
        'expires_at': expires_at.isoformat() if expires_at else None
    }
    
    response_ban = await client.post('/bans', 
                                     json=ban_data,
                                     headers={'Authorization': f'Bearer {admin_token}'})
    
    assert response_ban.status_code == 201
    data = response_ban.json()
    assert data['reason'] == reason
    assert data['user_id'] is not None


@pytest.mark.parametrize('telegram_id, username, role', [
    (200, 'BanUser01', 'Ученик'),
    (201, 'BanUser02', 'Преподаватель'),
    (202, 'BanUser03', 'Админ')
])
async def test_unban_user(client, admin_token, telegram_id, username, role):
    response_create = await client.post('/users/create',
                                        json={'telegram_id': telegram_id,
                                              'username': username,
                                              'role': role,
                                              'is_banned': False})
    assert response_create.status_code == 201

    ban_data = {
        'telegram_id': telegram_id,
        'reason': 'Test ban for unban',
        'expires_at': None
    }
    
    response_ban = await client.post('/bans',
                                     json=ban_data,
                                     headers={'Authorization': f'Bearer {admin_token}'})
    assert response_ban.status_code == 201

    response_unban = await client.delete(f'/bans/{telegram_id}',
                                         headers={'Authorization': f'Bearer {admin_token}'})
    
    assert response_unban.status_code == 204

    response_get_user = await client.get(f'/users/{telegram_id}')
    assert response_get_user.status_code == 200
    user_data = response_get_user.json()
    assert user_data['is_banned'] is False


async def test_get_ban_info(client, admin_token):
    telegram_id = 300
    username = 'GetBanUser'
    reason = 'Test reason'

    response_create = await client.post('/users/create',
                                        json={'telegram_id': telegram_id,
                                              'username': username,
                                              'role': 'Ученик',
                                              'is_banned': False})
    assert response_create.status_code == 201

    ban_data = {
        'telegram_id': telegram_id,
        'reason': reason,
        'expires_at': None
    }
    
    response_ban = await client.post('/bans',
                                     json=ban_data,
                                     headers={'Authorization': f'Bearer {admin_token}'})
    assert response_ban.status_code == 201

    response_get = await client.get(f'/bans/{telegram_id}',
                                    headers={'Authorization': f'Bearer {admin_token}'})
    
    assert response_get.status_code == 200
    data = response_get.json()
    assert data['telegram_id'] == telegram_id
    assert data['reason'] == reason
    assert data['is_banned'] is True


async def test_get_all_bans(client, admin_token):
    for i in range(3):
        telegram_id = 400 + i
        username = f'BanAllUser{i}'

        await client.post('/users/create',
                         json={'telegram_id': telegram_id,
                               'username': username,
                               'role': 'Ученик',
                               'is_banned': False})

        await client.post('/bans',
                         json={'telegram_id': telegram_id,
                               'reason': f'Reason {i}',
                               'expires_at': None},
                         headers={'Authorization': f'Bearer {admin_token}'})

    response = await client.get('/bans',
                               headers={'Authorization': f'Bearer {admin_token}'})
    
    assert response.status_code == 200
    bans = response.json()
    assert len(bans) >= 3


async def test_cannot_ban_already_banned_user(client, admin_token):
    telegram_id = 500
    username = 'DoubleBanUser'

    await client.post('/users/create',
                     json={'telegram_id': telegram_id,
                           'username': username,
                           'role': 'Ученик',
                           'is_banned': False})

    response_ban1 = await client.post('/bans',
                                      json={'telegram_id': telegram_id,
                                            'reason': 'First ban',
                                            'expires_at': None},
                                      headers={'Authorization': f'Bearer {admin_token}'})
    assert response_ban1.status_code == 201

    response_ban2 = await client.post('/bans',
                                      json={'telegram_id': telegram_id,
                                            'reason': 'Second ban',
                                            'expires_at': None},
                                      headers={'Authorization': f'Bearer {admin_token}'})
    assert response_ban2.status_code == 400
    assert 'already banned' in response_ban2.json()['detail']


async def test_cannot_unban_non_banned_user(client, admin_token):
    telegram_id = 600
    username = 'NonBannedUser'

    await client.post('/users/create',
                     json={'telegram_id': telegram_id,
                           'username': username,
                           'role': 'Ученик',
                           'is_banned': False})

    response = await client.delete(f'/bans/{telegram_id}',
                                   headers={'Authorization': f'Bearer {admin_token}'})
    
    assert response.status_code == 404
    assert 'not banned' in response.json()['detail']


async def test_ban_non_existent_user(client, admin_token):
    response = await client.post('/bans',
                                json={'telegram_id': 999999,
                                      'reason': 'Test',
                                      'expires_at': None},
                                headers={'Authorization': f'Bearer {admin_token}'})
    
    assert response.status_code == 404
    assert 'not found' in response.json()['detail']

