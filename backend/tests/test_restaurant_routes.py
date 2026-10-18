from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.services.auth import create_access_token, hash_password


def test_list_restaurants_returns_active_restaurants(client, db_session):
    db_session.add_all([
        Restaurant(name="Baraka Restaurant", slug="baraka-restaurant", is_active=True),
        Restaurant(name="Inactive Restaurant", slug="inactive-restaurant", is_active=False),
    ])
    db_session.commit()

    response = client.get("/restaurants")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Baraka Restaurant"
    assert data[0]["slug"] == "baraka-restaurant"


def test_get_restaurant_by_slug(client, db_session):
    db_session.add(
        Restaurant(
            name="Baraka Restaurant",
            slug="baraka-restaurant",
            is_active=True,
        )
    )
    db_session.commit()

    response = client.get("/restaurants/baraka-restaurant")

    assert response.status_code == 200
    assert response.json()["name"] == "Baraka Restaurant"


def test_inactive_restaurant_is_not_publicly_accessible(client, db_session):
    db_session.add(
        Restaurant(
            name="Inactive Restaurant",
            slug="inactive-restaurant",
            is_active=False,
        )
    )
    db_session.commit()

    response = client.get("/restaurants/inactive-restaurant")

    assert response.status_code == 404


def test_unknown_restaurant_returns_404(client):
    response = client.get("/restaurants/unknown-restaurant")

    assert response.status_code == 404


def test_customer_cannot_order_from_inactive_restaurant(client, db_session):
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.restaurant import Restaurant
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    user = User(
        name="Inactive Restaurant Test Customer",
        phone="09119990001",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.customer,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        name=user.name,
        phone=user.phone,
        user_id=user.id,
    )
    restaurant = Restaurant(
        name="Inactive Test Restaurant",
        slug="inactive-test-restaurant",
        is_active=False,
    )
    db_session.add_all([customer, restaurant])
    db_session.commit()

    token = create_access_token(user.id, "customer")
    headers = {"Authorization": f"Bearer {token}"}

    order_count_before = db_session.query(Order).count()

    response = client.post(
        "/restaurants/inactive-test-restaurant/orders",
        headers=headers,
        json={
            "address": "Test Address",
            "order_items": [{"food_id": 9999, "quantity": 1}],
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    assert db_session.query(Order).count() == order_count_before


def test_customer_cannot_create_restaurant(client, db_session):
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    user = User(
        name="Regular Customer",
        phone="09119990002",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.customer,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id, "customer")
    response = client.post(
        "/restaurants",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Unauthorized Restaurant", "slug": "unauthorized-restaurant"},
    )

    assert response.status_code == 403
    assert db_session.query(Restaurant).filter_by(
        slug="unauthorized-restaurant"
    ).first() is None


def test_customer_cannot_assign_restaurant_owner(client, db_session):
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    user = User(
        name="Regular Customer",
        phone="09119990003",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.customer,
    )
    restaurant = Restaurant(
        name="Owner Assignment Test",
        slug="owner-assignment-test",
        is_active=False,
    )
    db_session.add_all([user, restaurant])
    db_session.commit()

    token = create_access_token(user.id, "customer")
    response = client.put(
        f"/restaurants/{restaurant.id}/owner",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": user.id},
    )

    assert response.status_code == 403


def test_customer_cannot_change_restaurant_activation(client, db_session):
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    user = User(
        name="Regular Customer",
        phone="09119990004",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.customer,
    )
    restaurant = Restaurant(
        name="Activation Test",
        slug="activation-test",
        is_active=False,
    )
    db_session.add_all([user, restaurant])
    db_session.commit()

    token = create_access_token(user.id, "customer")
    response = client.patch(
        f"/restaurants/{restaurant.id}/activation",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": True},
    )

    db_session.refresh(restaurant)
    assert response.status_code == 403
    assert restaurant.is_active is False

def test_platform_admin_can_list_all_restaurants(client, db_session):
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    admin = User(
        name="Platform Admin",
        phone="09119990101",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.platform_admin,
    )
    restaurants = [
        Restaurant(
            name="Active Restaurant",
            slug="active-restaurant",
            is_active=True,
        ),
        Restaurant(
            name="Inactive Restaurant",
            slug="inactive-restaurant",
            is_active=False,
        ),
    ]
    db_session.add_all([admin, *restaurants])
    db_session.commit()

    token = create_access_token(admin.id, UserRole.platform_admin.value)
    response = client.get(
        "/restaurants/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {item["slug"] for item in data} == {
        "active-restaurant",
        "inactive-restaurant",
    }


def test_customer_cannot_list_all_restaurants_as_admin(client, db_session):
   
    customer = User(
        name="Regular Customer",
        phone="09119990102",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.customer,
    )
    db_session.add(customer)
    db_session.commit()

    token = create_access_token(customer.id, UserRole.customer.value)
    response = client.get(
        "/restaurants/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_all_restaurants(client):
    response = client.get("/restaurants/admin")

    assert response.status_code in (401, 403)


def test_platform_admin_can_get_inactive_restaurant_by_slug(
    client, db_session
):
    admin = User(
        name="Platform Admin",
        phone="09119990103",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.platform_admin,
    )
    restaurant = Restaurant(
        name="Inactive Restaurant",
        slug="admin-inactive-restaurant",
        is_active=False,
    )
    db_session.add_all([admin, restaurant])
    db_session.commit()

    token = create_access_token(admin.id, UserRole.platform_admin.value)
    response = client.get(
        "/restaurants/admin/admin-inactive-restaurant",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "admin-inactive-restaurant"
    assert response.json()["is_active"] is False