from app.models.user import User, UserRole
from app.services.auth import create_access_token, hash_password


def create_test_user(db_session, name, phone, role):
    user = User(
        name=name,
        phone=phone,
        password_hash=hash_password("TestPassword123"),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_platform_admin_can_list_users(client, db_session):
    admin = create_test_user(
        db_session,
        "Platform Admin",
        "09119990201",
        UserRole.platform_admin,
    )
    create_test_user(
        db_session,
        "Regular Customer",
        "09119990202",
        UserRole.customer,
    )

    token = create_access_token(
        admin.id,
        UserRole.platform_admin.value,
    )
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {user["name"] for user in data} == {
        "Platform Admin",
        "Regular Customer",
    }
    assert all("password_hash" not in user for user in data)
    assert all("password" not in user for user in data)


def test_customer_cannot_list_users(client, db_session):
    customer = create_test_user(
        db_session,
        "Regular Customer",
        "09119990203",
        UserRole.customer,
    )

    token = create_access_token(
        customer.id,
        UserRole.customer.value,
    )
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_users(client):
    response = client.get("/users/")

    assert response.status_code == 401
