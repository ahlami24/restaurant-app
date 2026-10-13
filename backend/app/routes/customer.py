import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.database import get_db
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer import (
    create_customer as create_customer_service,
    get_customers as get_customers_service,
    get_customer_by_id as get_customer_by_id_service,
    update_customer as update_customer_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# CREATE CUSTOMER
@router.post("/customers", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    try:
        new_customer = create_customer_service(db, customer)

        db.commit()
        db.refresh(new_customer)

        return new_customer

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Phone number already exists",
        )

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating customer")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


# GET ALL CUSTOMERS
@router.get("/customers", response_model=list[CustomerResponse])
def get_customers(db: Session = Depends(get_db)):
    try:
        return get_customers_service(db)

    except SQLAlchemyError:
        logger.exception("Database error while retrieving customers")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error",
        )


# GET CUSTOMER BY ID
@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
):
    try:
        customer = get_customer_by_id_service(db, customer_id)

        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        return customer

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
):
    try:
        updated_customer = update_customer_service(
            db,
            customer_id,
            customer_update,
        )

        if not updated_customer:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
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
