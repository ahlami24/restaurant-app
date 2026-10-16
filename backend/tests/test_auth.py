from datetime import timedelta, timezone, datetime

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

def test_auth_me_without_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_auth_me_with_expired_token_returns_401(client):

    import jwt

    from app.services.auth import ALGORITHM, SECRET_KEY

    expired_payload = {
        "sub": "1",
        "role": "customer",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(
        expired_payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


def test_auth_me_with_invalid_user_id_returns_401(client):
    import jwt

    from app.services.auth import ALGORITHM, SECRET_KEY

    payload = {
        "sub": "not-a-number",
        "role": "customer",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_register_user_without_email(client):
    response = client.post(
        "/users",
        json={
            "name": "No Email User",
            "phone": "0911000020",
            "password": "StrongTestPassword123",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] is None


def test_register_duplicate_email_returns_400(client):
    first_response = client.post(
        "/users",
        json={
            "name": "First User",
            "phone": "0911000021",
            "email": "duplicate@example.com",
            "password": "StrongTestPassword123",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/users",
        json={
            "name": "Second User",
            "phone": "0911000022",
            "email": "duplicate@example.com",
            "password": "StrongTestPassword123",
        },
    )

    assert second_response.status_code == 400


def test_register_invalid_email_returns_422(client):
    response = client.post(
        "/users",
        json={
            "name": "Invalid Email User",
            "phone": "0911000023",
            "email": "not-an-email",
            "password": "StrongTestPassword123",
        },
    )

    assert response.status_code == 422


def test_register_duplicate_email_with_different_case_returns_400(client):
    first_response = client.post(
        "/users",
        json={
            "name": "First Case User",
            "phone": "0911000024",
            "email": "CaseTest@example.com",
            "password": "StrongTestPassword123",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/users",
        json={
            "name": "Second Case User",
            "phone": "0911000025",
            "email": "casetest@EXAMPLE.com",
            "password": "StrongTestPassword123",
        },
    )

    assert second_response.status_code == 400


def test_login_with_legacy_phone_field(client):
    register_response = register_user(client)
    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "phone": "0911000010",
            "password": "StrongTestPassword123",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
