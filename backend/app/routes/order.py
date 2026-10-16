from app.schemas import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderItemUpdate
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.order import (
    create_order as create_order_service,
    update_order_status as update_order_status_service,
    get_orders as get_orders_service,
    get_order_by_id as get_order_by_id_service,
    update_order_items as update_order_items_service
)

from app.models.user import User
from app.routes.dependencies import get_current_user, require_role, get_restaurant_membership
from app.models.customer import Customer
from app.models.order import Order
from app.models.restaurant import Restaurant, RestaurantMembership
from sqlalchemy import select

router = APIRouter()

@router.post("/restaurants/{restaurant_slug}/orders", response_model=OrderResponse)
def create_order(
    restaurant_slug: str,
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
    ):
    restaurant = db.query(Restaurant).filter(
        Restaurant.slug == restaurant_slug,
        Restaurant.is_active.is_(True),
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail=f"Restaurant with slug '{restaurant_slug}' not found"
        )

    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:

        raise HTTPException(
            status_code=404,
            detail="Customer profile not found"
        )
    try:
        new_order = create_order_service(
            db, order, customer.id, restaurant.id
        )
        db.commit()
        db.refresh(new_order)
        return new_order

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )


@router.get("/orders", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value == "customer":
        customer = db.query(Customer).filter(
            Customer.user_id == current_user.id
        ).first()

        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer profile not found"
            )

        return get_orders_service(db, customer.id)

    if current_user.role.value == "delivery_person":
        restaurant_ids = select(
            RestaurantMembership.restaurant_id
            ).where(
                RestaurantMembership.user_id == current_user.id,
                RestaurantMembership.role == "delivery_person"
            )

        return db.query(Order).filter(
            Order.restaurant_id.in_(restaurant_ids),
            Order.status.in_(["ready", "out_for_delivery"])
        ).all()

    raise HTTPException(
        status_code=403,
        detail="You do not have permission to view orders"
    )

@router.get("/restaurants/{restaurant_slug}/orders", response_model=list[OrderResponse])
def get_restaurant_orders(
    restaurant_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: RestaurantMembership = Depends(get_restaurant_membership)
):
    return db.query(Order).filter(
        Order.restaurant_id == membership.restaurant_id
    ).all()

@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_role = current_user.role.value
    customer_id = None
    restaurant_id = None

    if user_role == "customer":
        customer = db.query(Customer).filter(
            Customer.user_id == current_user.id
        ).first()

        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer profile not found"
            )
        customer_id = customer.id

    elif user_role in ("restaurant_owner", "delivery_person"):
        membership = db.query(RestaurantMembership).filter(
                RestaurantMembership.user_id == current_user.id,
                RestaurantMembership.role.in_(
                    ["owner", "manager"]
                    if user_role == "restaurant_owner"
                    else ["delivery_person"]
                )
            ).all()
        if not membership:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to update order status"
            )
        restaurant_ids = [m.restaurant_id for m in membership]
    else:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update order status"
        )

    try:
        order = update_order_status_service(
            db=db,
            order_id=order_id,
            new_status=status_update.status,
            user_role=user_role,
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            restaurant_ids=restaurant_ids if user_role in ("restaurant_owner", "delivery_person") else None
        )
        db.commit()
        db.refresh(order)
        return order
    except PermissionError as e:
        db.rollback()
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )


@router.patch("/orders/{order_id}/items", response_model=OrderResponse)
def update_order_items(
    order_id: int,
    order_items: list[OrderItemUpdate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found for the current user"
        )

    try:
        order = update_order_items_service(
            db,
            order_id,
            customer.id,
            order_items
        )

        db.commit()
        db.refresh(order)

        return order

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )

