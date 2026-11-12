from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.customer import Customer
from app.models.delivery_person import DeliveryPerson
from app.models.order import Order
from app.models.restaurant import Restaurant, RestaurantMembership
from app.models.user import User
from app.routes.dependencies import (
    get_current_customer,
    get_current_delivery_person,
    get_current_user,
    get_restaurant_membership,
)
from app.schemas import OrderCreate, OrderItemUpdate, OrderResponse, OrderStatusUpdate
from app.services.order import (
    create_order as create_order_service,
)
from app.services.order import (
    get_orders as get_orders_service,
)
from app.services.order import (
    update_order_items as update_order_items_service,
)
from app.services.order import (
    update_order_status as update_order_status_service,
)

router = APIRouter()


@router.post("/restaurants/{restaurant_slug}/orders", response_model=OrderResponse, status_code=201)
def create_order(
    restaurant_slug: str,
    order: OrderCreate,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.slug == restaurant_slug,
        Restaurant.is_active.is_(True),
    ).first()
    if restaurant is None:
        raise HTTPException(status_code=404, detail=f"Restaurant with slug '{restaurant_slug}' not found")
    try:
        new_order = create_order_service(db, order, customer.id, restaurant.id)
        db.commit()
        db.refresh(new_order)
        return new_order
    except NotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


@router.get("/orders", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    return get_orders_service(db, customer.id)


@router.get("/delivery/orders", response_model=list[OrderResponse])
def get_delivery_orders(
    db: Session = Depends(get_db),
    delivery_person: DeliveryPerson = Depends(get_current_delivery_person),
):
    restaurant_ids = db.query(RestaurantMembership.restaurant_id).filter(
        RestaurantMembership.user_id == delivery_person.user_id,
        RestaurantMembership.role == "delivery_person",
    )
    return db.query(Order).filter(
        Order.restaurant_id.in_(restaurant_ids),
        Order.status.in_(["ready", "out_for_delivery"]),
    ).all()


@router.get("/restaurants/{restaurant_slug}/orders", response_model=list[OrderResponse])
def get_restaurant_orders(
    restaurant_slug: str,
    db: Session = Depends(get_db),
    membership: RestaurantMembership = Depends(get_restaurant_membership),
):
    return db.query(Order).filter(Order.restaurant_id == membership.restaurant_id).all()


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
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

    if new_status in ("preparing", "ready"):
        memberships = db.query(RestaurantMembership).filter(
            RestaurantMembership.user_id == current_user.id,
            RestaurantMembership.role.in_(["owner", "manager"]),
        ).all()
        if not memberships:
            raise HTTPException(status_code=403, detail="Restaurant owner or manager membership required")
        actor_type = "restaurant"
        restaurant_ids = {m.restaurant_id for m in memberships}

    elif new_status in ("out_for_delivery", "delivered"):
        delivery_person = db.query(DeliveryPerson).filter(
            DeliveryPerson.user_id == current_user.id
        ).first()
        if delivery_person is None:
            raise HTTPException(status_code=403, detail="Delivery person profile required")
        memberships = db.query(RestaurantMembership).filter(
            RestaurantMembership.user_id == current_user.id,
            RestaurantMembership.role == "delivery_person",
        ).all()
        if not memberships:
            raise HTTPException(status_code=403, detail="You are not assigned to any restaurant for delivery")
        actor_type = "delivery_person"
        restaurant_ids = {m.restaurant_id for m in memberships}

    elif new_status == "cancelled":
        target = db.query(Order).filter(Order.id == order_id).first()
        if target is None:
            raise HTTPException(status_code=404, detail="Order not found")
        staff = db.query(RestaurantMembership).filter(
            RestaurantMembership.user_id == current_user.id,
            RestaurantMembership.restaurant_id == target.restaurant_id,
            RestaurantMembership.role.in_(["owner", "manager"]),
        ).first()
        if staff is not None:
            actor_type = "restaurant"
            restaurant_ids = {target.restaurant_id}
        else:
            customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
            if customer is None or customer.id != target.customer_id:
                raise HTTPException(status_code=403, detail="Only the customer or this restaurant's staff can cancel the order")
            actor_type = "customer"
            customer_id = customer.id
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported order status: {new_status}")

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
    except NotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ForbiddenError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


@router.patch("/orders/{order_id}/items", response_model=OrderResponse)
def update_order_items(
    order_id: int,
    order_items: list[OrderItemUpdate] = Body(min_length=1),
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    try:
        order = update_order_items_service(db, order_id, customer.id, order_items)
        db.commit()
        db.refresh(order)
        return order
    except NotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc
