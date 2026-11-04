from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderItemUpdate,
)
from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_person import DeliveryPerson
from app.models.order import Order
from app.models.restaurant import Restaurant, RestaurantMembership
from app.routes.dependencies import (
    get_current_user,
    get_restaurant_membership,
)
from app.services.order import (
    create_order as create_order_service,
    update_order_status as update_order_status_service,
    get_orders as get_orders_service,
    update_order_items as update_order_items_service,
)

router = APIRouter()


def get_customer_profile(db: Session, user_id: int):
    return db.query(Customer).filter(
        Customer.user_id == user_id
    ).first()


def get_delivery_profile(db: Session, user_id: int):
    return db.query(DeliveryPerson).filter(
        DeliveryPerson.user_id == user_id
    ).first()


@router.post(
    "/restaurants/{restaurant_slug}/orders",
    response_model=OrderResponse,
)
def create_order(
    restaurant_slug: str,
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.slug == restaurant_slug,
        Restaurant.is_active.is_(True),
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail=f"Restaurant with slug '{restaurant_slug}' not found",
        )

    customer = get_customer_profile(db, current_user.id)

    if not customer:
        raise HTTPException(
            status_code=403,
            detail="Customer profile required to place an order",
        )

    try:
        new_order = create_order_service(
            db,
            order,
            customer.id,
            restaurant.id,
        )
        db.commit()
        db.refresh(new_order)
        return new_order

    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


# Customer order history
@router.get("/orders", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = get_customer_profile(db, current_user.id)

    if not customer:
        raise HTTPException(
            status_code=403,
            detail="Customer profile required to view customer orders",
        )

    return get_orders_service(db, customer.id)

@router.get("/delivery/orders", response_model=list[OrderResponse])
def get_delivery_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delivery_person = get_delivery_profile(db, current_user.id)

    if not delivery_person:
        raise HTTPException(
            status_code=403,
            detail="Delivery person profile required",
        )

    restaurant_ids = (
        db.query(RestaurantMembership.restaurant_id)
        .filter(
            RestaurantMembership.user_id == current_user.id,
            RestaurantMembership.role == "delivery_person",
        )
    )

    return (
        db.query(Order)
        .filter(
            Order.restaurant_id.in_(restaurant_ids),
            Order.status.in_(["ready", "out_for_delivery"]),
        )
        .all()
    )


@router.get(
    "/restaurants/{restaurant_slug}/orders",
    response_model=list[OrderResponse],
)
def get_restaurant_orders(
    restaurant_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: RestaurantMembership = Depends(get_restaurant_membership),
):
    return db.query(Order).filter(
        Order.restaurant_id == membership.restaurant_id
    ).all()


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderResponse,
)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_status = status_update.status.value

    customer_id = None
    restaurant_ids = None
    actor_type = None

    if new_status == "cancelled":
        customer = get_customer_profile(db, current_user.id)

        if not customer:
            raise HTTPException(
                status_code=403,
                detail="Customer profile required to cancel an order",
            )

        actor_type = "customer"
        customer_id = customer.id

    elif new_status in ("preparing", "ready"):
        memberships = (
            db.query(RestaurantMembership)
            .filter(
                RestaurantMembership.user_id == current_user.id,
                RestaurantMembership.role.in_(["owner", "manager"]),
            )
            .all()
        )

        if not memberships:
            raise HTTPException(
                status_code=403,
                detail="Restaurant owner or manager membership required",
            )

        actor_type = "restaurant"
        restaurant_ids = {membership.restaurant_id for membership in memberships}

    elif new_status in ("out_for_delivery", "delivered"):
        delivery_person = get_delivery_profile(db, current_user.id)

        if not delivery_person:
            raise HTTPException(
                status_code=403,
                detail="Delivery person profile required",
            )

        memberships = (
            db.query(RestaurantMembership)
            .filter(
                RestaurantMembership.user_id == current_user.id,
                RestaurantMembership.role == "delivery_person",
            )
            .all()
        )

        if not memberships:
            raise HTTPException(
                status_code=403,
                detail="You are not assigned to any restaurant for delivery",
            )

        actor_type = "delivery_person"
        restaurant_ids = {membership.restaurant_id for membership in memberships}

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported order status: {new_status}",
        )

    try:
        order = update_order_status_service(
            db=db,
            order_id=order_id,
            new_status=new_status,
            actor_type=actor_type,
            customer_id=customer_id,
            restaurant_ids=restaurant_ids,
        )

        db.commit()
        db.refresh(order)
        return order

    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc))

    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


@router.patch(
    "/orders/{order_id}/items",
    response_model=OrderResponse,
)
def update_order_items(
    order_id: int,
    order_items: list[OrderItemUpdate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = get_customer_profile(db, current_user.id)

    if not customer:
        raise HTTPException(
            status_code=403,
            detail="Customer profile required to update order items",
        )

    try:
        order = update_order_items_service(
            db,
            order_id,
            customer.id,
            order_items,
        )

        db.commit()
        db.refresh(order)
        return order

    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )