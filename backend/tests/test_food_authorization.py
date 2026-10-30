from app.models.restaurant import Restaurant, RestaurantMembership
from app.models.user import UserRole
from app.services.user import create_user as create_user_service
from app.models.food import Food
from app.models.customer import Customer
from app.models.order import Order

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

def test_delivery_person_only_sees_orders_from_assigned_restaurants(
    client, db_session
):
    delivery_person = create_user_service(
        db_session,
        "Test Delivery Person",
        "0911000030",
        UserRole.delivery_person,
        "StrongTestPassword123",
    )

    assigned_restaurant = Restaurant(
        name="Assigned Restaurant",
        slug="assigned-restaurant",
    )
    other_restaurant = Restaurant(
        name="Other Restaurant",
        slug="other-restaurant",
    )
    customer = Customer(
        name="Test Customer",
        phone="0911000031",
    )

    db_session.add_all([
        assigned_restaurant,
        other_restaurant,
        customer,
    ])
    db_session.flush()

    membership = RestaurantMembership(
        user_id=delivery_person.id,
        restaurant_id=assigned_restaurant.id,
        role="delivery_person",
    )
    db_session.add(membership)

    assigned_order = Order(
        customer_id=customer.id,
        restaurant_id=assigned_restaurant.id,
        address="Address 1",
        total_price=100,
        status="ready",
    )
    foreign_order = Order(
        customer_id=customer.id,
        restaurant_id=other_restaurant.id,
        address="Address 2",
        total_price=200,
        status="ready",
    )
    pending_order = Order(
        customer_id=customer.id,
        restaurant_id=assigned_restaurant.id,
        address="Address 3",
        total_price=50,
        status="pending",
    )

    db_session.add_all([
        assigned_order,
        foreign_order,
        pending_order,
    ])
    db_session.commit()

    login = client.post(
        "/auth/login",
        json={
            "phone": "0911000030",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.get(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    orders = response.json()

    assert [order["id"] for order in orders] == [assigned_order.id]

def test_delivery_person_can_update_orders_at_multiple_assigned_restaurants(
    client, db_session
):
    delivery_person = create_user_service(
        db_session,
        "Multi Restaurant Delivery",
        "0911000040",
        UserRole.delivery_person,
        "StrongTestPassword123",
    )

    restaurant_a = Restaurant(
        name="Restaurant A",
        slug="restaurant-a",
    )
    restaurant_b = Restaurant(
        name="Restaurant B",
        slug="restaurant-b",
    )
    restaurant_c = Restaurant(
        name="Restaurant C",
        slug="restaurant-c",
    )
    customer = Customer(
        name="Test Customer",
        phone="0911000041",
    )

    db_session.add_all([
        restaurant_a,
        restaurant_b,
        restaurant_c,
        customer,
    ])
    db_session.flush()

    db_session.add_all([
        RestaurantMembership(
            user_id=delivery_person.id,
            restaurant_id=restaurant_a.id,
            role="delivery_person",
        ),
        RestaurantMembership(
            user_id=delivery_person.id,
            restaurant_id=restaurant_b.id,
            role="delivery_person",
        ),
    ])

    order_a = Order(
        customer_id=customer.id,
        restaurant_id=restaurant_a.id,
        address="Address A",
        total_price=100,
        status="ready",
    )
    order_b = Order(
        customer_id=customer.id,
        restaurant_id=restaurant_b.id,
        address="Address B",
        total_price=200,
        status="ready",
    )
    order_c = Order(
        customer_id=customer.id,
        restaurant_id=restaurant_c.id,
        address="Address C",
        total_price=300,
        status="ready",
    )

    db_session.add_all([order_a, order_b, order_c])
    db_session.commit()

    order_a_id = order_a.id
    order_b_id = order_b.id
    order_c_id = order_c.id

    login = client.post(
        "/auth/login",
        json={
            "phone": "0911000040",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response_a = client.patch(
        f"/orders/{order_a_id}/status",
        json={"status": "out_for_delivery"},
        headers=headers,
    )
    assert response_a.status_code == 200
    assert response_a.json()["status"] == "out_for_delivery"

    response_b = client.patch(
        f"/orders/{order_b_id}/status",
        json={"status": "out_for_delivery"},
        headers=headers,
    )
    assert response_b.status_code == 200
    assert response_b.json()["status"] == "out_for_delivery"

    response_c = client.patch(
        f"/orders/{order_c_id}/status",
        json={"status": "out_for_delivery"},
        headers=headers,
    )
    assert response_c.status_code == 403

def test_food_search_is_case_insensitive(client, db_session):
    restaurant = Restaurant(name="Search Restaurant", slug="search-restaurant")
    db_session.add(restaurant)
    db_session.flush()

    db_session.add_all([
        Food(name="Chicken Burger", price=150, restaurant_id=restaurant.id),
        Food(name="Cheese Pizza", price=250, restaurant_id=restaurant.id),
    ])
    db_session.commit()

    response = client.get(
        "/restaurants/search-restaurant/foods?search=BURGER"
    )

    assert response.status_code == 200
    assert [food["name"] for food in response.json()] == ["Chicken Burger"]


def test_food_price_filter(client, db_session):
    restaurant = Restaurant(name="Price Restaurant", slug="price-restaurant")
    db_session.add(restaurant)
    db_session.flush()

    db_session.add_all([
        Food(name="Cheap Meal", price=50, restaurant_id=restaurant.id),
        Food(name="Medium Meal", price=150, restaurant_id=restaurant.id),
        Food(name="Expensive Meal", price=300, restaurant_id=restaurant.id),
    ])
    db_session.commit()

    response = client.get(
        "/restaurants/price-restaurant/foods?min_price=50&max_price=200"
    )

    assert response.status_code == 200
    assert {food["name"] for food in response.json()} == {
        "Cheap Meal",
        "Medium Meal",
    }


def test_food_search_and_price_filters_combine(client, db_session):
    restaurant = Restaurant(name="Combined Restaurant", slug="combined-restaurant")
    db_session.add(restaurant)
    db_session.flush()

    db_session.add_all([
        Food(name="Chicken Burger", price=150, restaurant_id=restaurant.id),
        Food(name="Beef Burger", price=300, restaurant_id=restaurant.id),
        Food(name="Chicken Pizza", price=180, restaurant_id=restaurant.id),
    ])
    db_session.commit()

    response = client.get(
        "/restaurants/combined-restaurant/foods"
        "?search=chicken&max_price=160"
    )

    assert response.status_code == 200
    assert [food["name"] for food in response.json()] == ["Chicken Burger"]


def test_food_filter_rejects_invalid_price_range(client, db_session):
    restaurant = Restaurant(name="Range Restaurant", slug="range-restaurant")
    db_session.add(restaurant)
    db_session.commit()

    response = client.get(
        "/restaurants/range-restaurant/foods?min_price=300&max_price=100"
    )

    assert response.status_code == 422

def test_food_category_filter_is_case_insensitive(client, db_session):
    restaurant = Restaurant(name="Category Restaurant", slug="category-restaurant")
    db_session.add(restaurant)
    db_session.flush()

    db_session.add_all([
        Food(name="Chicken Burger", price=150, category="breakfast", restaurant_id=restaurant.id),
        Food(name="Beef Burger", price=200, category="lunch", restaurant_id=restaurant.id),
        Food(name="Pancake", price=100, category="breakfast", restaurant_id=restaurant.id),
    ])
    db_session.commit()

    response = client.get(
        "/restaurants/category-restaurant/foods?category=BREAKFAST"
    )

    assert response.status_code == 200
    assert {food["name"] for food in response.json()} == {
        "Chicken Burger",
        "Pancake",
    }

def test_food_category_and_price_filters_combine(client, db_session):
    restaurant = Restaurant(name="Combined Category", slug="combined-category")
    db_session.add(restaurant)
    db_session.flush()

    db_session.add_all([
        Food(name="Chicken Burger", price=150, category="breakfast", restaurant_id=restaurant.id),
        Food(name="Pancake", price=100, category="breakfast", restaurant_id=restaurant.id),
        Food(name="Beef Burger", price=200, category="lunch", restaurant_id=restaurant.id),
    ])
    db_session.commit()

    response = client.get(
        "/restaurants/combined-category/foods?category=breakfast&max_price=120"
    )

    assert response.status_code == 200
    assert [food["name"] for food in response.json()] == ["Pancake"]

def test_food_sort_by_price_ascending(client, db_session):
    restaurant = Restaurant(name="Sorting Restaurant", slug="sorting-restaurant")
    db_session.add(restaurant)
    db_session.flush()

    db_session.add_all([
        Food(name="Pizza", price=250, restaurant_id=restaurant.id),
        Food(name="Burger", price=150, restaurant_id=restaurant.id),
        Food(name="Sandwich", price=100, restaurant_id=restaurant.id),
    ])
    db_session.commit()

    response = client.get(
        "/restaurants/sorting-restaurant/foods?sort_by=price_asc"
    )

    assert response.status_code == 200
    assert [food["name"] for food in response.json()] == [
        "Sandwich", "Burger", "Pizza"
    ]

def test_food_sort_by_price_descending(client, db_session):
    restaurant = Restaurant(name="Descending Restaurant", slug="descending-restaurant")
    db_session.add(restaurant)
    db_session.flush()

    db_session.add_all([
        Food(name="Pizza", price=250, restaurant_id=restaurant.id),
        Food(name="Burger", price=150, restaurant_id=restaurant.id),
        Food(name="Sandwich", price=100, restaurant_id=restaurant.id),
    ])
    db_session.commit()

    response = client.get(
        "/restaurants/descending-restaurant/foods?sort_by=price_desc"
    )

    assert response.status_code == 200
    assert [food["name"] for food in response.json()] == [
        "Pizza", "Burger", "Sandwich"
    ]


def test_creating_food_with_category(client, db_session):
    owner = create_user_service(
        db_session,
        "Category Owner",
        "0911000050",
        UserRole.restaurant_owner,
        "StrongTestPassword123",
    )
    db_session.commit()

    restaurant = Restaurant(
        name="Category Restaurant",
        slug="category-restaurant",
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
            "phone": "0911000050",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/restaurants/category-restaurant/foods",
        json={"name": "Vegan Salad", "price": 12.50, "category": "vegan"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Vegan Salad"
    assert response.json()["category"] == "vegan"

def test_updating_food_category(client, db_session):
    owner = create_user_service(
        db_session,
        "Update Category Owner",
        "0911000060",
        UserRole.restaurant_owner,
        "StrongTestPassword123",
    )
    db_session.commit()

    restaurant = Restaurant(
        name="Update Category Restaurant",
        slug="update-category-restaurant",
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

    food = Food(name="Old Salad", price=10.00, category="salad", restaurant_id=restaurant.id)
    db_session.add(food)
    db_session.commit()

    login = client.post(
        "/auth/login",
        json={
            "phone": "0911000060",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.patch(
        f"/restaurants/update-category-restaurant/foods/{food.id}",
        json={"category": "vegan"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["category"] == "vegan"

def test_clearing_existing_food_category(client, db_session):
    owner = create_user_service(
        db_session,
        "Null Category Owner",
        "0911000070",
        UserRole.restaurant_owner,
        "StrongTestPassword123",
    )
    db_session.commit()

    restaurant = Restaurant(
        name="Null Category Restaurant",
        slug="null-category-restaurant",
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
            "phone": "0911000070",
            "password": "StrongTestPassword123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/restaurants/null-category-restaurant/foods",
        json={
            "name": "Mystery Dish",
            "price": 15.00,
            "category": "salad",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["category"] == "salad"

    food = response.json()

    clear_response = client.patch(
        f"/restaurants/null-category-restaurant/foods/{food['id']}",
        json={"category": None},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert clear_response.status_code == 200
    assert clear_response.json()["category"] is None