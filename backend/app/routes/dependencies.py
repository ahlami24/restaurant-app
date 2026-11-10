from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.delivery_person import DeliveryPerson
from app.models.restaurant import Restaurant, RestaurantMembership
from app.models.user import User, UserRole
from app.services.auth import decode_access_token


security = HTTPBearer()


def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


def require_role(required_role: str):
    """Check a platform-level role, not a user capability."""

    def role_checker(
        current_user: User = Depends(get_current_user),
    ):
        if current_user.role.value != required_role:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource",
            )

        return current_user

    return role_checker


def require_platform_admin(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.platform_admin:
        raise HTTPException(
            status_code=403,
            detail="Platform administrator access required",
        )

    return current_user


def get_current_customer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Customer:
    customer = (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=403,
            detail="Customer profile required",
        )

    return customer


def get_current_delivery_person(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeliveryPerson:
    delivery_person = (
        db.query(DeliveryPerson)
        .filter(DeliveryPerson.user_id == current_user.id)
        .first()
    )

    if delivery_person is None:
        raise HTTPException(
            status_code=403,
            detail="Delivery person profile required",
        )

    return delivery_person


def get_restaurant_membership(
    restaurant_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.slug == restaurant_slug)
        .first()
    )

    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    membership = (
        db.query(RestaurantMembership)
        .filter(
            RestaurantMembership.user_id == current_user.id,
            RestaurantMembership.restaurant_id == restaurant.id,
        )
        .first()
    )

    if membership is None or membership.role not in ("owner", "manager"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this restaurant",
        )

    return membership