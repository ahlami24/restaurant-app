from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.delivery_person import DeliveryPerson
from app.models.restaurant import Restaurant, RestaurantMembership
from app.schemas.user import (
    UserCreate,
    UserResponse,
    RestaurantOwnerRegistration,
    RestaurantOwnerRegistrationResponse,
)
from app.services.user import create_user as create_user_service
from app.routes.dependencies import get_current_user, require_role


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)



@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_customer(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        new_user = create_user_service(
            db,
            user.name,
            user.phone,
            UserRole.user,
            user.password,
            email=user.email,
        )

        db.add(Customer(user_id=new_user.id))
        db.commit()
        db.refresh(new_user)

        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number or email already exists",
        )


@router.post(
    "/delivery-person",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_delivery_person(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        new_user = create_user_service(
            db,
            user.name,
            user.phone,
            UserRole.user,
            user.password,
            email=user.email,
        )

        db.add(DeliveryPerson(user_id=new_user.id))
        db.commit()
        db.refresh(new_user)

        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number or email already exists",
        )


@router.post(
    "/me/delivery-profile",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_delivery_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_profile = (
        db.query(DeliveryPerson)
        .filter(DeliveryPerson.user_id == current_user.id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery person profile already exists",
        )

    try:
        db.add(DeliveryPerson(user_id=current_user.id))
        db.commit()
        db.refresh(current_user)

        return current_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery person profile already exists",
        )


@router.post(
    "/restaurant-owner",
    response_model=RestaurantOwnerRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_restaurant_owner(
    registration: RestaurantOwnerRegistration,
    db: Session = Depends(get_db),
):
    try:
        new_user = create_user_service(
            db,
            registration.user.name,
            registration.user.phone,
            UserRole.user,
            registration.user.password,
            email=registration.user.email,
        )

        db.add(Customer(user_id=new_user.id))

        new_restaurant = Restaurant(
            name=registration.restaurant.name,
            slug=registration.restaurant.slug,
            is_active=False,
        )
        db.add(new_restaurant)
        db.flush()

        db.add(
            RestaurantMembership(
                user_id=new_user.id,
                restaurant_id=new_restaurant.id,
                role="owner",
            )
        )

        db.commit()

        db.refresh(new_user)
        db.refresh(new_restaurant)

        return {
            "user": new_user,
            "restaurant": new_restaurant,
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Phone number, email, or restaurant slug already exists"
            ),
        )


@router.get(
    "/",
    response_model=list[UserResponse],
)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.platform_admin.value)
    ),
):
    return db.query(User).order_by(User.id.asc()).all()