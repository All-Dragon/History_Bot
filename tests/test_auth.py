TEST_PASSWORD = "test-password-123"


async def test_login_token(client, mocker):
    await client.post(
        "/users/create",
        json={
            "telegram_id": 777,
            "username": "Test",
            "role": "Ученик",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )

    mock_token = mocker.patch("app.services.auth.create_access_token")
    mock_token.return_value = "fake"

    response = await client.post(
        "/auth/login",
        json={"telegram_id": 777, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json().get("access_token") == "fake"


async def test_error_login_token(client, mocker):
    await client.post(
        "/users/create",
        json={
            "telegram_id": 777,
            "username": "Test",
            "role": "Ученик",
            "is_banned": False,
            "password": TEST_PASSWORD,
        },
    )

    mock_token = mocker.patch("app.services.auth.create_access_token")
    mock_token.side_effect = Exception("Ошибка генерации токена")

    response = await client.post(
        "/auth/login",
        json={"telegram_id": 777, "password": TEST_PASSWORD},
    )
    assert response.status_code != 200
