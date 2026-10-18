from app.models.user import User, UserRole
from app.services.auth import create_access_token
from app.models.customer import Customer

def test_create_customer(client, db_session):
    response = client.post(
        "/users",
        json={
            "name": "Test Customer",
            "phone": "0911000001",
            "password": "test-password",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Customer"
    assert response.json()["phone"] == "0911000001"
    assert response.json()["role"] == "customer"

    customer = (
        db_session.query(Customer)
        .filter(Customer.user_id == response.json()["id"])
        .first()
    )

    assert customer is not None
    assert customer.name == "Test Customer"
    assert customer.phone == "0911000001"

def test_get_customers(client, db_session):
    created = client.post(
        "/users",
        json={
            "name": "Customer One", 
            "phone": "0911000002",
            "password": "test-password",
            },
    )

    assert created.status_code == 200

    admin = User(
        name="Test Admin",
        phone="0900000001",
        password_hash="test-hash",
        role=UserRole.platform_admin,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token(admin.id, admin.role.value)

    response = client.get(
        "/customers",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Customer One"

def test_get_customer_by_id(client, db_session):
    created = client.post(
        "/users",
        json={
            "name": "Customer Two",
            "phone": "0911000003",
            "password": "test-password",
        },
    )
    assert created.status_code == 200

    customer = (
        db_session.query(Customer)
        .filter(Customer.user_id == created.json()["id"])
        .first()
    )
    assert customer is not None
    customer_id = customer.id

    admin = User(
        name="Test Admin",
        phone="0900000002",
        password_hash="test-hash",
        role=UserRole.platform_admin,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token(admin.id, admin.role.value)

    response = client.get(
        f"/customers/{customer_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Customer Two"


def test_get_missing_customer_returns_404(client, db_session):
    admin = User(
        name="Test Admin",
        phone="0900000003",
        password_hash="test-hash",
        role=UserRole.platform_admin,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token(admin.id, admin.role.value)

    response = client.get(
        "/customers/9999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_duplicate_phone_returns_400(client):
    payload = {
        "name": "First Customer",
        "phone": "0911000004",
        "password": "test-password",
    }

    first_response = client.post("/users", json=payload)

    second_response = client.post(
        "/users",
        json={
            "name": "Second Customer",
            "phone": payload["phone"],
            "password": "another-password",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400


def test_update_customer(client, db_session):
    created = client.post(
        "/users",
        json={
            "name": "Old Name",
            "phone": "0911000005",
            "password": "test-password",
        },
    )
    assert created.status_code == 200

    customer = (
        db_session.query(Customer)
        .filter(Customer.user_id == created.json()["id"])
        .first()
    )
    assert customer is not None
    customer_id = customer.id

    admin = User(
        name="Test Admin",
        phone="0900000004",
        password_hash="test-hash",
        role=UserRole.platform_admin,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = create_access_token(admin.id, admin.role.value)

    response = client.put(
        f"/customers/{customer_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to update this customer"
    )

    db_session.refresh(customer)
    assert customer.name == "Old Name"
    assert customer.phone == "0911000005"