from app.models.customer import Customer
from app.models.user import User, UserRole
from app.services.auth import create_access_token


def test_create_customer(client, db_session):
    response = client.post(
        "/users",
        json={
            "name": "Test Customer",
            "phone": "0911000001",
            "password": "test-password",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Customer"
    assert response.json()["phone"] == "0911000001"
    assert response.json()["role"] == "user"

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

    assert created.status_code == 201

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
    assert created.status_code == 201

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

    assert first_response.status_code == 201
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
    assert created.status_code == 201

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

def test_customer_phone_update_changes_login_identifier(client, db_session):
    password = "StrongTestPassword123"
    created = client.post(
        "/users",
        json={
            "name": "Phone Update Customer",
            "phone": "0911000091",
            "password": password,
        },
    )
    assert created.status_code == 201
    customer = db_session.query(Customer).filter_by(
        user_id=created.json()["id"]
    ).first()
    token = create_access_token(created.json()["id"], UserRole.user.value)

    updated = client.put(
        f"/customers/{customer.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"phone": "0911000092"},
    )
    assert updated.status_code == 200
    assert updated.json()["phone"] == "0911000092"

    old_login = client.post(
        "/auth/login",
        json={"identifier": "0911000091", "password": password},
    )
    new_login = client.post(
        "/auth/login",
        json={"identifier": "0911000092", "password": password},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200
