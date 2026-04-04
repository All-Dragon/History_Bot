import pytest_asyncio

TEST_PASSWORD = "test-password-123"


@pytest_asyncio.fixture
async def created_question(client):
    response_create = await client.post(
        "/users/create",
        json={
            "telegram_id": 101,
            "username": "IVAN",
            "role": "Преподаватель",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )
    token_response = await client.post(
        "/auth/login",
        json={
            "telegram_id": response_create.json().get("telegram_id", 101),
            "password": TEST_PASSWORD,
        },
    )
    token = token_response.json()["access_token"]

    actual_user_id = response_create.json()["id"]

    response = await client.post(
        "/question/new",
        json={
            "text": "Тестовый вопрос",
            "options": None,
            "correct_answer": "correct_answer",
            "topic": "topic",
            "difficulty": 5,
            "created_by": actual_user_id,
            "image_url": None,
            "status": "published",
            "question_type": "free_text",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json(), token


@pytest_asyncio.fixture
async def created_answer(client):
    response_create = await client.post(
        "/users/create",
        json={
            "telegram_id": 102,
            "username": "OLEG",
            "role": "Админ",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )
    token_response = await client.post(
        "/auth/login",
        json={
            "telegram_id": response_create.json().get("telegram_id", 102),
            "password": TEST_PASSWORD,
        },
    )
    token = token_response.json()["access_token"]

    actual_user_id = response_create.json()["id"]

    response = await client.post(
        "/question/new",
        json={
            "text": "Тестовый вопрос",
            "options": None,
            "correct_answer": "correct_answer",
            "topic": "topic",
            "difficulty": 5,
            "created_by": actual_user_id,
            "image_url": None,
            "status": "published",
            "question_type": "free_text",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    question = response.json()
    response = await client.post(
        "/answers/create",
        json={
            "question_id": question.get("id"),
            "answer": question.get("correct_answer"),
            "is_correct": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json(), token


async def test_create_answer(client, created_question):
    question, token = created_question
    response = await client.post(
        "/answers/create",
        json={
            "question_id": question.get("id"),
            "answer": question.get("correct_answer"),
            "is_correct": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


async def test_get_answer_by_id(client, created_answer):
    answer, token = created_answer
    response = await client.get(
        f"/answers/{answer.get('id', 1)}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest_asyncio.fixture
async def created_answer_all(client):
    response_create = await client.post(
        "/users/create",
        json={
            "telegram_id": 103,
            "username": "ANNA",
            "role": "Админ",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )
    token_response = await client.post(
        "/auth/login",
        json={
            "telegram_id": response_create.json().get("telegram_id", 103),
            "password": TEST_PASSWORD,
        },
    )
    token = token_response.json()["access_token"]

    actual_user_id = response_create.json()["id"]

    response = await client.post(
        "/question/new",
        json={
            "text": "Тестовый вопрос",
            "options": None,
            "correct_answer": "correct_answer",
            "topic": "topic",
            "difficulty": 5,
            "created_by": actual_user_id,
            "image_url": None,
            "status": "published",
            "question_type": "free_text",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    question = response.json()
    response = await client.post(
        "/answers/create",
        json={
            "question_id": question.get("id"),
            "answer": question.get("correct_answer"),
            "is_correct": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json(), token


async def test_get_all_answer(client, created_answer_all):
    _, token = created_answer_all
    response = await client.get(
        "/answers",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
