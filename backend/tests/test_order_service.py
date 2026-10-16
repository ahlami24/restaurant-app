import pytest

from app.models.customer import Customer
from app.models.food import Food
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.restaurant import Restaurant
from app.services.order import update_order_items


@pytest.fixture
def order_setup(db_session):
    restaurant = Restaurant(
        name="Test Restaurant",
        slug="test-restaurant",
        is_active=True,
    )
    other_restaurant = Restaurant(
        name="Other Restaurant",
        slug="other-restaurant",
        is_active=True,
    )
    customer = Customer(
        name="Test Customer",
        phone="0912345678",
    )

    db_session.add_all([restaurant, other_restaurant, customer])
    db_session.flush()

    food1 = Food(
        name="Burger",
        price=100,
        restaurant_id=restaurant.id,
    )
    food2 = Food(
        name="Pizza",
        price=200,
        restaurant_id=restaurant.id,
    )
    foreign_food = Food(
        name="Foreign Food",
        price=50,
        restaurant_id=other_restaurant.id,
    )

    db_session.add_all([food1, food2, foreign_food])
    db_session.flush()

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address="Test Address",
        total_price=300,
        status="pending",
    )
    db_session.add(order)
    db_session.flush()

    order.order_items.extend([
        OrderItem(food_id=food1.id, quantity=1, price=100),
        OrderItem(food_id=food2.id, quantity=1, price=200),
    ])
    db_session.commit()

    return {
        "order": order,
        "food1": food1,
        "food2": food2,
        "foreign_food": foreign_food,
        "customer": customer,
    }


def test_update_rejects_food_from_another_restaurant(
    db_session, order_setup
):
    data = order_setup

    with pytest.raises(ValueError, match="does not exist in this restaurant"):
        update_order_items(
            db_session,
            data["order"].id,
            data["customer"].id,
            [
                type("Item", (), {
                    "food_id": data["foreign_food"].id,
                    "quantity": 1,
                })()
            ],
        )


def test_update_removes_omitted_items(db_session, order_setup):
    data = order_setup

    updated_order = update_order_items(
        db_session,
        data["order"].id,
        data["customer"].id,
        [
            type("Item", (), {
                "food_id": data["food1"].id,
                "quantity": 2,
            })()
        ],
    )

    assert len(updated_order.order_items) == 1
    assert updated_order.order_items[0].food_id == data["food1"].id
    assert updated_order.total_price == 200


def test_update_recalculates_total(db_session, order_setup):
    data = order_setup

    updated_order = update_order_items(
        db_session,
        data["order"].id,
        data["customer"].id,
        [
            type("Item", (), {
                "food_id": data["food1"].id,
                "quantity": 3,
            })(),
            type("Item", (), {
                "food_id": data["food2"].id,
                "quantity": 2,
            })(),
        ],
    )

    assert updated_order.total_price == 700


def test_update_rejects_duplicate_food_ids(db_session, order_setup):
    data = order_setup

    duplicate_item = type("Item", (), {
        "food_id": data["food1"].id,
        "quantity": 1,
    })()

    with pytest.raises(ValueError, match="Duplicate food_id"):
        update_order_items(
            db_session,
            data["order"].id,
            data["customer"].id,
            [duplicate_item, duplicate_item],
        )