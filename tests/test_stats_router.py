import random

import pytest
import pytest_asyncio

TEST_PASSWORD = "test-password-123"


@pytest_asyncio.fixture
async def teacher_with_token(client):
    telegram_id = random.randint(50000, 59999)

    response = await client.post(
        "/users/create",
        json={
            "telegram_id": telegram_id,
            "username": "Teacher",
            "role": "Преподаватель",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )

    token_response = await client.post(
        "/auth/login",
        json={"telegram_id": telegram_id, "password": TEST_PASSWORD},
    )
    return {
        "telegram_id": telegram_id,
        "token": token_response.json()["access_token"],
        "user_id": response.json()["id"],
    }


@pytest_asyncio.fixture
async def admin_with_token(client):
    telegram_id = random.randint(60000, 69999)

    response = await client.post(
        "/users/create",
        json={
            "telegram_id": telegram_id,
            "username": "AdminStats",
            "role": "Админ",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )

    token_response = await client.post(
        "/auth/login",
        json={"telegram_id": telegram_id, "password": TEST_PASSWORD},
    )
    return {
        "telegram_id": telegram_id,
        "token": token_response.json()["access_token"],
        "user_id": response.json()["id"],
    }


@pytest_asyncio.fixture
async def student_with_token(client):
    telegram_id = random.randint(70000, 79999)

    response = await client.post(
        "/users/create",
        json={
            "telegram_id": telegram_id,
            "username": "Student",
            "role": "Ученик",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )

    token_response = await client.post(
        "/auth/login",
        json={"telegram_id": telegram_id, "password": TEST_PASSWORD},
    )
    return {
        "telegram_id": telegram_id,
        "token": token_response.json()["access_token"],
        "user_id": response.json()["id"],
    }


@pytest_asyncio.fixture
async def published_question(client, teacher_with_token):
    teacher = teacher_with_token

    response = await client.post(
        "/question/new",
        json={
            "text": "Тестовый вопрос для статистики",
            "options": None,
            "correct_answer": "correct",
            "topic": "stats_topic",
            "difficulty": 3,
            "created_by": teacher["user_id"],
            "image_url": None,
            "status": "published",
            "question_type": "free_text",
        },
        headers={"Authorization": f"Bearer {teacher['token']}"},
    )

    return response.json()


async def test_get_my_stats_empty(client, student_with_token):
    response = await client.get(
        "/stats/my_stats",
        headers={"Authorization": f"Bearer {student_with_token['token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_question"] == 0
    assert data["right_answer"] == 0
    assert data["right_answer_percentage"] == "0.0%"


@pytest.mark.parametrize(
    "num_answers, correct_answers",
    [(5, 3), (10, 7), (3, 0), (1, 1)],
)
async def test_get_my_stats_with_answers(client, student_with_token, teacher_with_token, num_answers, correct_answers):
    question_ids = []
    for i in range(num_answers):
        response = await client.post(
            "/question/new",
            json={
                "text": f"Вопрос {i + 1}",
                "options": None,
                "correct_answer": "correct",
                "topic": "stats_test",
                "difficulty": 1,
                "created_by": teacher_with_token["user_id"],
                "image_url": None,
                "status": "published",
                "question_type": "free_text",
            },
            headers={"Authorization": f"Bearer {teacher_with_token['token']}"},
        )
        question_ids.append(response.json()["id"])

    for idx, question_id in enumerate(question_ids):
        await client.post(
            "/answers/create",
            json={
                "question_id": question_id,
                "answer": "test answer",
                "is_correct": idx < correct_answers,
            },
            headers={"Authorization": f"Bearer {student_with_token['token']}"},
        )

    response = await client.get(
        "/stats/my_stats",
        headers={"Authorization": f"Bearer {student_with_token['token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_question"] == num_answers
    assert data["right_answer"] == correct_answers

    expected_percentage = round(correct_answers / num_answers * 100, 2) if num_answers > 0 else 0.0
    assert data["right_answer_percentage"] == f"{expected_percentage}%"


async def test_get_admin_overview(client, admin_with_token):
    for i in range(3):
        await client.post(
            "/users/create",
            json={
                "telegram_id": 1000 + i,
                "username": f"OverviewUser{i}",
                "role": "Ученик",
                "is_banned": False,
                "password": TEST_PASSWORD,
            },
        )

    response = await client.get(
        "/stats/admin/overview",
        headers={"Authorization": f"Bearer {admin_with_token['token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_user" in data
    assert "current_user" in data
    assert "deleted_user" in data
    assert data["total_user"] >= 3
    assert data["current_user"] >= 3
    assert isinstance(data["deleted_user"], int)


async def test_admin_overview_unauthorized(client, student_with_token):
    response = await client.get(
        "/stats/admin/overview",
        headers={"Authorization": f"Bearer {student_with_token['token']}"},
    )
    assert response.status_code == 403


async def test_get_question_answers(client, teacher_with_token, student_with_token, published_question):
    question_id = published_question["id"]

    await client.post(
        "/answers/create",
        json={
            "question_id": question_id,
            "answer": "first answer",
            "is_correct": True,
        },
        headers={"Authorization": f"Bearer {student_with_token['token']}"},
    )

    response = await client.get(
        f"/stats/questions/{question_id}/answers",
        headers={"Authorization": f"Bearer {teacher_with_token['token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["is_correct"] is True


async def test_teacher_cannot_see_other_teacher_answers(client, teacher_with_token):
    teacher2_id = random.randint(80000, 89999)
    await client.post(
        "/users/create",
        json={
            "telegram_id": teacher2_id,
            "username": "Teacher2",
            "role": "Преподаватель",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )

    teacher2_response = await client.post(
        "/auth/login",
        json={"telegram_id": teacher2_id, "password": TEST_PASSWORD},
    )
    teacher2_token = teacher2_response.json()["access_token"]

    question_response = await client.post(
        "/question/new",
        json={
            "text": "Question for teacher1",
            "options": None,
            "correct_answer": "answer",
            "topic": "test",
            "difficulty": 1,
            "created_by": teacher_with_token["user_id"],
            "image_url": None,
            "status": "published",
            "question_type": "free_text",
        },
        headers={"Authorization": f"Bearer {teacher_with_token['token']}"},
    )
    question_id = question_response.json()["id"]

    response = await client.get(
        f"/stats/questions/{question_id}/answers",
        headers={"Authorization": f"Bearer {teacher2_token}"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "deleted_count, expected_deleted",
    [(0, 0), (1, 1), (2, 2)],
)
async def test_admin_overview_with_deleted_users(client, admin_with_token, deleted_count, expected_deleted):
    for i in range(deleted_count + 1):
        telegram_id = 2000 + i
        await client.post(
            "/users/create",
            json={
                "telegram_id": telegram_id,
                "username": f"DeleteUser{i}",
                "role": "Ученик",
                "is_banned": False,
                "password": TEST_PASSWORD,
            },
        )

        if i < deleted_count:
            token_response = await client.post(
                "/auth/login",
                json={"telegram_id": telegram_id, "password": TEST_PASSWORD},
            )
            token = token_response.json()["access_token"]
            await client.delete(
                "/users/soft_del",
                headers={"Authorization": f"Bearer {token}"},
            )

    response = await client.get(
        "/stats/admin/overview",
        headers={"Authorization": f"Bearer {admin_with_token['token']}"},
    )

    assert response.status_code == 200
    assert response.json()["deleted_user"] >= expected_deleted


async def test_get_answers_no_permission(client, student_with_token, published_question):
    response = await client.get(
        f"/stats/questions/{published_question['id']}/answers",
        headers={"Authorization": f"Bearer {student_with_token['token']}"},
    )
    assert response.status_code == 403


async def test_get_my_stats_unauthorized(client):
    response = await client.get("/stats/my_stats")
    assert response.status_code == 401
