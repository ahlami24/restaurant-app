from app.models.restaurant import Restaurant, RestaurantMembership
from app.models.user import UserRole
from app.services.user import create_user as create_user_service
from app.models.food import Food

def test_customer_cannot_create_food(client, db_session):
    registration = client.post(
        "/users",
        json={
            "name": "Test Customer",
            "phone": "0911000020",
            "password": "StrongTestPassword123",
        },
    )
    assert registration.status_code == 200
    restaurant = Restaurant(
        name="Test Restaurant",
        slug="test-restaurant",
    )
    db_session.add(restaurant)
    db_session.commit()

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
        "/restaurants/test-restaurant/foods",
        json={"name": "Test Pizza", "price": 12.50},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403



def test_restaurant_owner_can_create_food(client, db_session):
    owner = create_user_service(
        db_session,
        "Test Owner",
        "0911000021",
        UserRole.restaurant_owner,
        "StrongTestPassword123",
    )
    db_session.commit()

    restaurant = Restaurant(
        name="Test Restaurant",
        slug="test-restaurant",
    )
    db_session.add(restaurant)
    db_session.commit()

    membership = RestaurantMembership(
        user_id=owner.id,
        restaurant_id=restaurant.id,
        role="owner",
    )
    db_session.add(membership)
    db_session.commit()

    login = client.post(
        "/auth/login",
        json={
            "phone": "0911000021",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/restaurants/test-restaurant/foods",
        json={"name": "Test Pizza", "price": 12.50},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Pizza"

def test_restaurant_menu_only_shows_its_own_foods(client, db_session):
    restaurant1 = Restaurant(name="Restaurant 1", slug="restaurant-1")
    restaurant2 = Restaurant(name="Restaurant 2", slug="restaurant-2")
    db_session.add_all([restaurant1, restaurant2])
    db_session.commit()

    food1 = Food(name="Food 1", price=10.0, restaurant_id=restaurant1.id)
    food2 = Food(name="Food 2", price=15.0, restaurant_id=restaurant2.id)
    db_session.add_all([food1, food2])
    db_session.commit()

    response1 = client.get("/restaurants/restaurant-1/foods")
    assert response1.status_code == 200
    foods = response1.json()
    assert len(foods) == 1
    assert foods[0]["name"] == "Food 1"

def test_restaurant_cannot_access_other_restaurant_food(client, db_session):
    restaurant1 = Restaurant(name="Restaurant 1", slug="restaurant-1")
    restaurant2 = Restaurant(name="Restaurant 2", slug="restaurant-2")
    db_session.add_all([restaurant1, restaurant2])
    db_session.commit()

    food1 = Food(name="Food 1", price=10.0, restaurant_id=restaurant1.id)
    db_session.add(food1)
    db_session.commit()

    response = client.get(f"/restaurants/restaurant-2/foods/{food1.id}")
    assert response.status_code == 404