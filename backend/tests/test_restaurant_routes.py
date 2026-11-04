from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.services.auth import create_access_token, hash_password
from app.models.delivery_person import DeliveryPerson

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

    user = User(
        name="Inactive Restaurant Test Customer",
        phone="09119990001",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(user_id=user.id)

    restaurant = Restaurant(
        name="Inactive Test Restaurant",
        slug="inactive-test-restaurant",
        is_active=False,
    )

    db_session.add_all([customer, restaurant])
    db_session.commit()

    token = create_access_token(user.id, UserRole.user.value)
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
    user = User(
        name="Regular Customer",
        phone="09119990002",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id, UserRole.user.value)
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
    user = User(
        name="Regular Customer",
        phone="09119990003",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant = Restaurant(
        name="Owner Assignment Test",
        slug="owner-assignment-test",
        is_active=False,
    )
    db_session.add_all([user, restaurant])
    db_session.commit()

    token = create_access_token(user.id, UserRole.user.value)
    response = client.put(
        f"/restaurants/{restaurant.id}/owner",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": user.id},
    )

    assert response.status_code == 403


def test_customer_cannot_change_restaurant_activation(client, db_session):
    user = User(
        name="Regular Customer",
        phone="09119990004",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant = Restaurant(
        name="Activation Test",
        slug="activation-test",
        is_active=False,
    )
    db_session.add_all([user, restaurant])
    db_session.commit()

    token = create_access_token(user.id, UserRole.user.value)
    response = client.patch(
        f"/restaurants/{restaurant.id}/activation",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": True},
    )

    db_session.refresh(restaurant)
    assert response.status_code == 403
    assert restaurant.is_active is False


def test_platform_admin_can_list_all_restaurants(client, db_session):
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
        role=UserRole.user,
    )
    db_session.add(customer)
    db_session.commit()

    token = create_access_token(customer.id, UserRole.user.value)
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


def test_restaurant_owner_can_assign_customer_as_delivery_person(
    client, db_session
):
    from app.models.customer import Customer
    from app.models.restaurant import RestaurantMembership

    owner = User(
        name="Restaurant Owner",
        phone="09119990201",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )

    customer = User(
        name="Delivery Candidate",
        phone="09119990202",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )

    restaurant = Restaurant(
        name="Delivery Test Restaurant",
        slug="delivery-test-restaurant",
        is_active=True,
    )

    db_session.add_all([owner, customer, restaurant])
    db_session.flush()

    customer_profile = Customer(user_id=customer.id)
    delivery_profile = DeliveryPerson(user_id=customer.id)

    owner_membership = RestaurantMembership(
        user_id=owner.id,
        restaurant_id=restaurant.id,
        role="owner",
    )

    db_session.add_all([
        customer_profile,
        delivery_profile,
        owner_membership,
    ])
    db_session.commit()

    token = create_access_token(owner.id, UserRole.user.value)

    response = client.post(
        f"/restaurants/{restaurant.id}/delivery-person",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": customer.id},
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Delivery person assigned successfully",
        "user_id": customer.id,
        "restaurant_id": restaurant.id,
        "role": "delivery_person",
    }

    db_session.refresh(customer)

    assert customer.role == UserRole.user
    assert customer.customer is not None
    assert customer.delivery_person is not None

    membership = db_session.query(RestaurantMembership).filter_by(
        user_id=customer.id,
        restaurant_id=restaurant.id,
    ).first()

    assert membership is not None
    assert membership.role == "delivery_person"

def test_customer_cannot_assign_delivery_person(client, db_session):
    from app.models.restaurant import Restaurant
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    customer = User(
        name="Regular Customer",
        phone="09119990203",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant = Restaurant(
        name="Customer Access Test",
        slug="customer-access-test",
    )

    db_session.add_all([customer, restaurant])
    db_session.commit()

    token = create_access_token(
        customer.id,
        UserRole.user.value,
    )

    response = client.post(
        f"/restaurants/{restaurant.id}/delivery-person",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": customer.id},
    )

    assert response.status_code == 403


def test_owner_cannot_assign_delivery_person_to_another_restaurant(
    client, db_session
):
    from app.models.restaurant import Restaurant, RestaurantMembership
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    owner = User(
        name="First Restaurant Owner",
        phone="09119990204",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    candidate = User(
        name="Delivery Candidate",
        phone="09119990205",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )

    owned_restaurant = Restaurant(
        name="First Owner Restaurant",
        slug="first-owner-restaurant",
    )
    target_restaurant = Restaurant(
        name="Second Owner Restaurant",
        slug="second-owner-restaurant",
    )

    db_session.add_all([
        owner,
        candidate,
        owned_restaurant,
        target_restaurant,
    ])
    db_session.flush()
    db_session.add_all([
        DeliveryPerson(user_id=candidate.id),
        RestaurantMembership(
            user_id=owner.id,
            restaurant_id=owned_restaurant.id,
            role="owner",
        ),
    ])
    db_session.commit()

    token = create_access_token(
        owner.id,
        UserRole.user.value,
    )

    response = client.post(
        f"/restaurants/{target_restaurant.id}/delivery-person",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": candidate.id},
    )

    assert response.status_code == 403

    db_session.refresh(candidate)
    assert candidate.role == UserRole.user
    assert candidate.delivery_person is not None

    membership = db_session.query(RestaurantMembership).filter_by(
        user_id=candidate.id,
        restaurant_id=target_restaurant.id,
    ).first()

    assert membership is None


def test_cannot_assign_same_delivery_person_twice(client, db_session):
    from app.models.restaurant import Restaurant, RestaurantMembership
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    owner = User(
        name="Duplicate Test Owner",
        phone="09119990206",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    candidate = User(
        name="Duplicate Test Candidate",
        phone="09119990207",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant = Restaurant(
        name="Duplicate Assignment Restaurant",
        slug="duplicate-assignment-restaurant",
    )

    db_session.add_all([owner, candidate, restaurant])
    db_session.flush()

    db_session.add_all([
        DeliveryPerson(user_id=candidate.id),
        RestaurantMembership(
            user_id=owner.id,
            restaurant_id=restaurant.id,
            role="owner",
        ),
    ])
    db_session.commit()

    token = create_access_token(
        owner.id,
        UserRole.user.value,
    )
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"user_id": candidate.id}
    url = f"/restaurants/{restaurant.id}/delivery-person"

    first_response = client.post(url, headers=headers, json=payload)
    second_response = client.post(url, headers=headers, json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    db_session.refresh(candidate)
    assert candidate.role == UserRole.user

    memberships = db_session.query(RestaurantMembership).filter_by(
        user_id=candidate.id,
        restaurant_id=restaurant.id,
    ).all()

    assert len(memberships) == 1
    assert memberships[0].role == "delivery_person"

def test_delivery_person_can_be_assigned_to_multiple_restaurants(
    client, db_session
):
    from app.models.restaurant import Restaurant, RestaurantMembership
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    owner = User(
        name="Multi Restaurant Owner",
        phone="09119990208",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    candidate = User(
        name="Multi Restaurant Delivery Person",
        phone="09119990209",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant_one = Restaurant(
        name="First Delivery Restaurant",
        slug="first-delivery-restaurant",
    )
    restaurant_two = Restaurant(
        name="Second Delivery Restaurant",
        slug="second-delivery-restaurant",
    )

    db_session.add_all([
        owner,
        candidate,
        restaurant_one,
        restaurant_two,
    ])
    db_session.flush()

    db_session.add_all([
        DeliveryPerson(user_id=candidate.id),
        RestaurantMembership(
            user_id=owner.id,
            restaurant_id=restaurant_one.id,
            role="owner",
        ),
        RestaurantMembership(
            user_id=owner.id,
            restaurant_id=restaurant_two.id,
            role="owner",
        ),
    ])
    db_session.commit()

    token = create_access_token(
        owner.id,
        UserRole.user.value,
    )
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"user_id": candidate.id}

    first_response = client.post(
        f"/restaurants/{restaurant_one.id}/delivery-person",
        headers=headers,
        json=payload,
    )
    second_response = client.post(
        f"/restaurants/{restaurant_two.id}/delivery-person",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    db_session.refresh(candidate)

    # Restaurant-specific assignments must not change the platform role.
    assert candidate.role == UserRole.user
    assert candidate.delivery_person is not None

    memberships = db_session.query(RestaurantMembership).filter_by(
        user_id=candidate.id,
        role="delivery_person",
    ).all()

    assert len(memberships) == 2
    assert {
        membership.restaurant_id for membership in memberships
    } == {restaurant_one.id, restaurant_two.id}


def test_cannot_assign_platform_admin_as_delivery_person(
    client, db_session
):
    from app.models.restaurant import Restaurant, RestaurantMembership
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    owner = User(
        name="Assignment Protection Owner",
        phone="09119990210",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    admin = User(
        name="Platform Administrator",
        phone="09119990211",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.platform_admin,
    )
    restaurant = Restaurant(
        name="Assignment Protection Restaurant",
        slug="assignment-protection-restaurant",
    )

    db_session.add_all([owner, admin, restaurant])
    db_session.flush()

    db_session.add(
        RestaurantMembership(
            user_id=owner.id,
            restaurant_id=restaurant.id,
            role="owner",
        )
    )
    db_session.commit()

    token = create_access_token(
        owner.id,
        UserRole.user.value,
    )

    response = client.post(
        f"/restaurants/{restaurant.id}/delivery-person",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": admin.id},
    )

    assert response.status_code == 400

    db_session.refresh(admin)
    assert admin.role == UserRole.platform_admin

    membership = db_session.query(RestaurantMembership).filter_by(
        user_id=admin.id,
        restaurant_id=restaurant.id,
    ).first()

    assert membership is None

def test_assign_nonexistent_user_as_delivery_person_returns_404(
    client, db_session
):
    from app.models.restaurant import Restaurant, RestaurantMembership
    from app.models.user import User, UserRole
    from app.services.auth import create_access_token, hash_password

    owner = User(
        name="Missing User Test Owner",
        phone="09119990212",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant = Restaurant(
        name="Missing User Test Restaurant",
        slug="missing-user-test-restaurant",
    )

    db_session.add_all([owner, restaurant])
    db_session.flush()

    db_session.add(
        RestaurantMembership(
            user_id=owner.id,
            restaurant_id=restaurant.id,
            role="owner",
        )
    )
    db_session.commit()

    token = create_access_token(
        owner.id,
        UserRole.user.value,
    )

    response = client.post(
        f"/restaurants/{restaurant.id}/delivery-person",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    membership = db_session.query(RestaurantMembership).filter_by(
        restaurant_id=restaurant.id,
        user_id=999999,
    ).first()

    assert membership is None

def test_restaurant_owner_can_list_assigned_delivery_persons(
    client, db_session
):
    from app.models.restaurant import RestaurantMembership

    owner = User(
        name="Restaurant Owner",
        phone="09119990301",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    assigned_delivery = User(
        name="Assigned Delivery",
        phone="09119990302",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    unassigned_delivery = User(
        name="Unassigned Delivery",
        phone="09119990303",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )

    restaurant = Restaurant(
        name="Delivery Listing Restaurant",
        slug="delivery-listing-restaurant",
        is_active=True,
    )

    db_session.add_all([
        owner,
        assigned_delivery,
        unassigned_delivery,
        restaurant,
    ])
    db_session.flush()

    db_session.add_all([
        DeliveryPerson(user_id=assigned_delivery.id),
        DeliveryPerson(user_id=unassigned_delivery.id),
        RestaurantMembership(
            user_id=owner.id,
            restaurant_id=restaurant.id,
            role="owner",
        ),
        RestaurantMembership(
            user_id=assigned_delivery.id,
            restaurant_id=restaurant.id,
            role="delivery_person",
        ),
    ])
    db_session.commit()

    token = create_access_token(owner.id, UserRole.user.value)

    response = client.get(
        f"/restaurants/{restaurant.id}/delivery-persons",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    assert data[0]["user_id"] == assigned_delivery.id
    assert data[0]["name"] == "Assigned Delivery"
    assert data[0]["phone"] == "09119990302"
    assert data[0]["restaurants"] == [
        {
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "restaurant_slug": restaurant.slug,
        }
    ]

def test_regular_user_cannot_list_restaurant_delivery_persons(
    client, db_session
):
    user = User(
        name="Regular User",
        phone="09119990304",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant = Restaurant(
        name="Protected Restaurant",
        slug="protected-restaurant",
        is_active=True,
    )

    db_session.add_all([user, restaurant])
    db_session.commit()

    token = create_access_token(user.id, UserRole.user.value)

    response = client.get(
        f"/restaurants/{restaurant.id}/delivery-persons",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

def test_delivery_person_cannot_list_restaurant_delivery_persons(
    client, db_session
):
    delivery_user = User(
        name="Delivery User",
        phone="09119990305",
        password_hash=hash_password("TestPassword123"),
        role=UserRole.user,
    )
    restaurant = Restaurant(
        name="Delivery Protected Restaurant",
        slug="delivery-protected-restaurant",
        is_active=True,
    )

    db_session.add_all([delivery_user, restaurant])
    db_session.flush()

    db_session.add(
        DeliveryPerson(user_id=delivery_user.id)
    )
    db_session.commit()

    token = create_access_token(
        delivery_user.id,
        UserRole.user.value,
    )

    response = client.get(
        f"/restaurants/{restaurant.id}/delivery-persons",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
