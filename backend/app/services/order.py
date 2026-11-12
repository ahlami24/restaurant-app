from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.customer import Customer
from app.models.food import Food
from app.models.order import Order
from app.models.order_item import OrderItem

ALLOWED_TRANSITIONS = {
    "pending": {
        "preparing": {"restaurant"},
        "cancelled": {"customer", "restaurant"},
    },
    "preparing": {
        "ready": {"restaurant"},
        "cancelled": {"restaurant"},
    },
    "ready": {"out_for_delivery": {"delivery_person"}},
    "out_for_delivery": {"delivered": {"delivery_person"}},
}


def create_order(db, order, customer_id, restaurant_id):
    new_order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        address=order.address,
        total_price=0,
        status="pending",
    )

    food_ids = [item.food_id for item in order.order_items]

    if len(set(food_ids)) != len(food_ids):
        raise ValueError(
            "Duplicate food_id found in order_items. "
            "Each food_id must be unique."
        )

    customer = db.query(Customer).filter(
        Customer.id == customer_id
    ).first()

    if not customer:
        raise NotFoundError(f"Customer with id {customer_id} does not exist")

    food_prices = {
        food.id: food.price
        for food in db.query(Food)
        .filter(
            Food.id.in_(food_ids),
            Food.restaurant_id == restaurant_id,
        )
        .all()
    }

    for item in order.order_items:
        if item.food_id not in food_prices:
            raise NotFoundError(
                f"Food with id {item.food_id} does not exist in this restaurant"
            )

    db.add(new_order)
    db.flush()

    for item in order.order_items:
        new_order.order_items.append(
            OrderItem(
                food_id=item.food_id,
                quantity=item.quantity,
                price=food_prices[item.food_id],
            )
        )

    new_order.total_price = sum(
        item.price * item.quantity
        for item in new_order.order_items
    )

    return new_order


def get_orders(db, customer_id):
    return (
        db.query(Order)
        .filter(Order.customer_id == customer_id)
        .all()
    )


def get_order_by_id(db, order_id, customer_id):
    return (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.customer_id == customer_id,
        )
        .first()
    )


def update_order_status(
    db,
    order_id,
    new_status,
    actor_type,
    customer_id=None,
    restaurant_ids=None,
):
    if hasattr(new_status, "value"):
        new_status = new_status.value
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise NotFoundError(f"Order with id {order_id} does not exist")

    allowed_actors = ALLOWED_TRANSITIONS.get(order.status, {}).get(new_status)
    if allowed_actors is None:
        raise ConflictError(
            f"Cannot transition from '{order.status}' to '{new_status}'"
        )
    if actor_type not in allowed_actors:
        raise ForbiddenError(
            f"Actor type '{actor_type}' is not allowed to transition from "
            f"'{order.status}' to '{new_status}'"
        )

    if actor_type == "customer":
        if order.customer_id != customer_id:
            raise ForbiddenError("You do not have permission to update this order")
    elif actor_type in ("restaurant", "delivery_person"):
        if not restaurant_ids or order.restaurant_id not in restaurant_ids:
            raise ForbiddenError("You do not have permission to update this order")

    order.status = new_status
    return order


def update_order_items(db, order_id, customer_id, items):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.customer_id == customer_id,
    ).first()

    if not items:
        raise ValueError("An order must contain at least one item")
    if not order:
        raise NotFoundError("Order not found")

    if order.status != "pending":
        raise ConflictError("Only pending orders can be updated")

    food_ids = [item.food_id for item in items]

    if len(food_ids) != len(set(food_ids)):
        raise ValueError(
            "Duplicate food_id found. Each food_id must be unique."
        )

    food_prices = {
        food.id: food.price
        for food in db.query(Food).filter(
            Food.id.in_(food_ids),
            Food.restaurant_id == order.restaurant_id,
        ).all()
    }

    for food_id in food_ids:
        if food_id not in food_prices:
            raise NotFoundError(
                f"Food with id {food_id} does not exist in this restaurant"
            )

    existing_items = {
        item.food_id: item
        for item in order.order_items
    }
    requested_food_ids = set(food_ids)

    for food_id, existing_item in existing_items.items():
        if food_id not in requested_food_ids:
            order.order_items.remove(existing_item)

    for item in items:
        if item.food_id in existing_items:
            existing_item = existing_items[item.food_id]
            existing_item.quantity = item.quantity
            existing_item.price = food_prices[item.food_id]
        else:
            order.order_items.append(
                OrderItem(
                    food_id=item.food_id,
                    quantity=item.quantity,
                    price=food_prices[item.food_id],
                )
            )

    order.total_price = sum(
        item.price * item.quantity
        for item in order.order_items
    )

    return order