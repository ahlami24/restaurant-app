from app.models.user import UserRole
from app.services.user import create_user as create_user_service


def test_customer_cannot_create_food(client):
    registration = client.post(
        "/users",
        json={
            "name": "Test Customer",
            "phone": "0911000020",
            "password": "StrongTestPassword123",
        },
    )
    assert registration.status_code == 200

    login = client.post(
        "/auth/login",
        json={
            "identifier": "0911000020",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.post(
        "/foods/",
        json={"name": "Test Pizza", "price": 12.50},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_restaurant_owner_can_create_food(client, db_session):
    create_user_service(
        db_session,
        "Test Owner",
        "0911000021",
        UserRole.restaurant_owner,
        "StrongTestPassword123",
    )
    db_session.commit()

    login = client.post(
        "/auth/login",
        json={
            "identifier": "0911000021",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.post(
        "/foods/",
        json={"name": "Test Pizza", "price": 12.50},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Pizza"
    assert response.json()["price"] == 12.50
