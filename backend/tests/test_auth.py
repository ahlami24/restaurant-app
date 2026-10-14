from app.services.auth import verify_password


def register_user(client):
    return client.post(
        "/users",
        json={
            "name": "Test User",
            "phone": "0911000010",
            "email": "Test@Example.com",
            "password": "StrongTestPassword123",
        },
    )


def test_register_user(client):
    response = register_user(client)

    assert response.status_code == 200
    assert response.json()["name"] == "Test User"
    assert response.json()["email"] == "test@example.com"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_login_with_phone(client):
    register_response = register_user(client)
    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "identifier": "0911000010",
            "password": "StrongTestPassword123",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_email(client):
    register_response = register_user(client)
    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "identifier": "test@example.com",
            "password": "StrongTestPassword123",
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password(client):
    register_response = register_user(client)
    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "identifier": "0911000010",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_password_hash_verification():
    from app.services.auth import hash_password

    password = "StrongTestPassword123"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("WrongPassword", password_hash)


def test_auth_me_with_valid_token(client):
    register_response = register_user(client)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "identifier": "0911000010",
            "password": "StrongTestPassword123",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "0911000010"
    assert response.json()["email"] == "test@example.com"


def test_auth_me_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401