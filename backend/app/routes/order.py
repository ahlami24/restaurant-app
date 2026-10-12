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
from app.routes.dependencies import get_current_user
from app.models.customer import Customer
from app.models.order import Order

router = APIRouter()

@router.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found for the current user")
        new_order = create_order_service(db, order, customer.id)
        db.commit()
        db.refresh(new_order)
        return new_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise
    except Exception as e:
        db.rollback()
        print("ORDER ERROR:", repr(e))
        raise HTTPException(
            status_code=500,
            detail=str(e)
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

    elif current_user.role.value == "restaurant_owner":
        return db.query(Order).all()

    elif current_user.role.value == "delivery_person":
        return db.query(Order).filter(
            Order.status.in_(["ready", "out_for_delivery"]))

    else:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view orders"
        )

@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        order = update_order_status_service(
            db,
            order_id,
            status_update.status,
            current_user.role.value
        )

        db.commit()
        db.refresh(order)

        return order

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

    