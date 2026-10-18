import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database import get_db
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.models.restaurant import RestaurantMembership
from app.models.order import Order
from app.routes.dependencies import get_current_user
from app.schemas.customer import (
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer import (
    get_customers as get_customers_service,
    get_customer_by_id as get_customer_by_id_service,
    update_customer as update_customer_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()

def customer_belongs_to_owner_restaurant(
        db: Session,
        owner_id: int,
        customer_id: int
) -> bool:
    restaurant_ids = (

        db.query(RestaurantMembership.restaurant_id)
        .filter(
            RestaurantMembership.user_id == owner_id,
            RestaurantMembership.role == "owner"
        )
        .subquery()
    )

    order_exists = (
        db.query(Order.id)
        .filter(
            Order.customer_id == customer_id,
            Order.restaurant_id.in_(restaurant_ids)
        )
        .first()
    )

    return order_exists is not None

@router.get("/customers", response_model=list[CustomerResponse])
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        if current_user.role == UserRole.platform_admin:
            return get_customers_service(db)
        if current_user.role == UserRole.restaurant_owner:
            restaurant_ids = (
                db.query(RestaurantMembership.restaurant_id)
                .filter(
                    RestaurantMembership.user_id == current_user.id,
                    RestaurantMembership.role == "owner"
                )
                .subquery()
            )

            return (
                db.query(Customer)
                .join(Order, Customer.id == Order.customer_id)
                .filter(Order.restaurant_id.in_(restaurant_ids))
                .distinct()
                .all()
            )
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to list customers",
        )

    except HTTPException:
        raise

    except SQLAlchemyError:
        logger.exception("Database error while retrieving customers")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        customer = get_customer_by_id_service(db, customer_id)

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        if current_user.role == UserRole.platform_admin:
            return customer

        if current_user.role == UserRole.customer:
            if customer.user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to view this customer",
                )
            return customer

        if current_user.role == UserRole.restaurant_owner:
            if customer_belongs_to_owner_restaurant(
                db,
                current_user.id,
                customer.id,
            ):
                return customer

            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view this customer",
            )

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this customer",
        )

    except HTTPException:
        raise

    except SQLAlchemyError:
        logger.exception("Database error while retrieving customer")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


# UPDATE CUSTOMER
@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        existing_customer = get_customer_by_id_service(db, customer_id)

        if existing_customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        # Platform administrators can update any customer.
        if current_user.role == UserRole.platform_admin:
            pass

        # Customers can update only their own profile.
        elif current_user.role == UserRole.customer:
            if existing_customer.user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to update this customer",
                )

        # Restaurant owners can update customers associated
        # with restaurants they own.
        elif current_user.role == UserRole.restaurant_owner:
            if not customer_belongs_to_owner_restaurant(
                db,
                current_user.id,
                existing_customer.id,
            ):
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to update this customer",
                )

        else:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to update this customer",
            )

        updated_customer = update_customer_service(
            db,
            customer_id,
            customer_update,
        )

        db.commit()
        db.refresh(updated_customer)

        return updated_customer

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Phone number already exists",
        )

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating customer")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )