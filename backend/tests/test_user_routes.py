from app.models.customer import Customer
from app.models.delivery_person import DeliveryPerson
from app.models.restaurant import Restaurant, RestaurantMembership
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
        "Regular User",
        "09119990202",
        UserRole.user,
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
        "Regular User",
    }
    assert all("password_hash" not in user for user in data)
    assert all("password" not in user for user in data)


def test_regular_user_cannot_list_users(client, db_session):
    user = create_test_user(
        db_session,
        "Regular User",
        "09119990203",
        UserRole.user,
    )

    token = create_access_token(
        user.id,
        UserRole.user.value,
    )
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_users(client):
    response = client.get("/users/")

    assert response.status_code == 401


def test_user_can_create_delivery_profile(client, db_session):
    user = create_test_user(
        db_session,
        "Customer Delivery Candidate",
        "09119990301",
        UserRole.user,
    )

    db_session.add(Customer(user_id=user.id))
    db_session.commit()

    token = create_access_token(user.id, UserRole.user.value)

    response = client.post(
        "/users/me/delivery-profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == user.id
    assert response.json()["role"] == UserRole.user.value

    delivery_profile = (
        db_session.query(DeliveryPerson).filter_by(user_id=user.id).first()
    )

    customer_profile = db_session.query(Customer).filter_by(user_id=user.id).first()

    assert delivery_profile is not None
    assert customer_profile is not None


def test_user_cannot_create_duplicate_delivery_profile(client, db_session):
    user = create_test_user(
        db_session,
        "Existing Delivery Candidate",
        "09119990302",
        UserRole.user,
    )

    db_session.add(DeliveryPerson(user_id=user.id))
    db_session.commit()

    token = create_access_token(user.id, UserRole.user.value)

    response = client.post(
        "/users/me/delivery-profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == ("Delivery person profile already exists")

    assert db_session.query(DeliveryPerson).filter_by(user_id=user.id).count() == 1


def test_unauthenticated_user_cannot_create_delivery_profile(client):
    response = client.post("/users/me/delivery-profile")

    assert response.status_code == 401


def test_restaurant_owner_registration_creates_all_records(client, db_session):
    response = client.post(
        "/users/restaurant-owner",
        json={
            "user": {
                "name": "New Restaurant Owner",
                "phone": "09119990303",
                "password": "SecurePassword123",
                "email": "owner@example.com",
            },
            "restaurant": {
                "name": "New Restaurant",
                "slug": "new-restaurant",
            },
        },
    )

    assert response.status_code == 201

    data = response.json()
    user_id = data["user"]["id"]
    restaurant_id = data["restaurant"]["id"]

    assert data["user"]["role"] == UserRole.user.value
    assert data["user"]["email"] == "owner@example.com"
    assert data["restaurant"]["slug"] == "new-restaurant"
    assert data["restaurant"]["is_active"] is False
    public_restaurants = client.get("/restaurants/")
    public_slugs = [restaurant["slug"] for restaurant in public_restaurants.json()]
    assert "new-restaurant" not in public_slugs

    user = db_session.query(User).filter_by(id=user_id).first()
    assert user is not None
    assert user.role == UserRole.user

    customer = db_session.query(Customer).filter_by(user_id=user_id).first()
    assert customer is not None

    membership = (
        db_session.query(RestaurantMembership)
        .filter_by(
            user_id=user_id,
            restaurant_id=restaurant_id,
        )
        .first()
    )

    assert membership is not None
    assert membership.role == "owner"

    assert "password_hash" not in data["user"]
    assert "password" not in data["user"]


def test_owner_registration_rolls_back_when_slug_already_exists(client, db_session):
    existing_restaurant = Restaurant(
        name="Existing Restaurant",
        slug="already-used-slug",
    )
    db_session.add(existing_restaurant)
    db_session.commit()

    user_count_before = db_session.query(User).count()
    customer_count_before = db_session.query(Customer).count()

    response = client.post(
        "/users/restaurant-owner",
        json={
            "user": {
                "name": "Rollback Test Owner",
                "phone": "09119990304",
                "password": "SecurePassword123",
            },
            "restaurant": {
                "name": "Another Restaurant",
                "slug": "already-used-slug",
            },
        },
    )

    assert response.status_code == 400

    assert db_session.query(User).count() == user_count_before
    assert db_session.query(Customer).count() == customer_count_before

    assert db_session.query(User).filter_by(phone="09119990304").first() is None

    assert (
        db_session.query(RestaurantMembership)
        .filter_by(restaurant_id=existing_restaurant.id)
        .count()
        == 0
    )
