import random

import pytest
import pytest_asyncio

TEST_PASSWORD = "test-password-123"


@pytest_asyncio.fixture
async def auth_token(client):
    telegram_id = random.randint(10000, 99999)

    data = {
        "telegram_id": telegram_id,
        "username": "Ivan",
        "role": "Преподаватель",
        "is_banned": False,
        "password": TEST_PASSWORD,
    }
    await client.post("/users/create", json=data)

    token_response = await client.post(
        "/auth/login",
        json={"telegram_id": telegram_id, "password": TEST_PASSWORD},
    )
    return token_response.json()["access_token"]


@pytest.mark.parametrize(
    "telegram_id, username, role, is_banned",
    [
        (0, "Olef", "Ученик", False),
        (1, "Ivan", "Преподаватель", False),
        (2, "Igor", "Админ", False),
    ],
)
async def test_create_user(telegram_id, username, role, is_banned, client):
    response = await client.post(
        "/users/create",
        json={
            "telegram_id": telegram_id,
            "username": username,
            "role": role,
            "is_banned": is_banned,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["telegram_id"] == telegram_id
    assert data["username"] == username
    assert data["role"] == role
    assert data["is_banned"] == is_banned


async def test_get_user_info(auth_token, client):
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200


@pytest.mark.parametrize("new_name", ("Oleg", "Igor"))
async def test_change_name(new_name, auth_token, client):
    response = await client.put(
        "/users/me/name",
        json={"name": new_name},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    assert response.json().get("username") == new_name


@pytest.mark.parametrize(
    "telegram_id, username, role, is_banned",
    [
        (3, "Igor", "Ученик", False),
        (4, "Anna", "Преподаватель", False),
        (5, "Vladimir", "Админ", False),
    ],
)
async def test_soft_delete(client, telegram_id, username, role, is_banned):
    await client.post(
        "/users/create",
        json={
            "telegram_id": telegram_id,
            "username": username,
            "role": role,
            "is_banned": is_banned,
            "password": TEST_PASSWORD,
        },
    )

    token_response = await client.post(
        "/auth/login",
        json={"telegram_id": telegram_id, "password": TEST_PASSWORD},
    )
    token = token_response.json()["access_token"]

    response = await client.delete(
        "/users/soft_del",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.parametrize(
    "telegram_id, username, role, is_banned",
    [
        (6, "John", "Ученик", False),
        (7, "Adda", "Преподаватель", False),
        (8, "Ado", "Админ", False),
    ],
)
async def test_restore_user(client, telegram_id, username, role, is_banned):
    await client.post(
        "/users/create",
        json={
            "telegram_id": telegram_id,
            "username": username,
            "role": role,
            "is_banned": is_banned,
            "password": TEST_PASSWORD,
        },
    )
    token_response = await client.post(
        "/auth/login",
        json={"telegram_id": telegram_id, "password": TEST_PASSWORD},
    )
    token = token_response.json()["access_token"]

    await client.delete(
        "/users/soft_del",
        headers={"Authorization": f"Bearer {token}"},
    )
    response_restore = await client.put(
        "/users/restore_user",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_restore.status_code == 200
    assert response_restore.json().get("deleted_at") is None


async def test_create_user_duplicate(client):
    user_payload = {
        "telegram_id": 200,
        "username": "Jin",
        "role": "Ученик",
        "is_banned": False,
        "password": TEST_PASSWORD,
    }
    await client.post("/users/create", json=user_payload)
    response = await client.post("/users/create", json=user_payload)

    assert response.status_code == 400
    assert response.json().get("detail") == "Пользователь уже существует!"


async def test_get_user_info_no_token(client):
    response = await client.get("/users/me")
    assert response.status_code == 401
