from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.restaurant import Restaurant, RestaurantMembership
from app.models.user import User, UserRole
from app.routes.dependencies import (
    get_current_user,
    require_platform_admin,
)
from app.schemas.restaurant import (
    DeliveryPersonAssign,
    DeliveryPersonAssignmentResponse,
    RestaurantActivationUpdate,
    RestaurantCreate,
    RestaurantOwnerAssign,
    RestaurantResponse,
)
from app.services.restaurant import (
    get_restaurants as get_restaurants_service,
    get_restaurant_by_slug as get_restaurant_by_slug_service,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=list[RestaurantResponse])
def get_restaurants(db: Session = Depends(get_db)):
    return get_restaurants_service(db)

@router.get("/admin", response_model=list[RestaurantResponse])
def get_all_restaurants(
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    return db.query(Restaurant).order_by(Restaurant.id.asc()).all()

@router.get("/admin/{restaurant_slug}", response_model=RestaurantResponse)
def get_restaurant_by_slug_admin(
    restaurant_slug: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    restaurant = db.query(Restaurant).filter(Restaurant.slug == restaurant_slug).first()

    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return restaurant

@router.get("/{restaurant_slug}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_slug: str,
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant_by_slug_service(db, restaurant_slug)

    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return restaurant


@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=201,
)
def create_restaurant(
    data: RestaurantCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    existing = db.query(Restaurant).filter(
        Restaurant.slug == data.slug
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="A restaurant with this slug already exists",
        )

    restaurant = Restaurant(
        name=data.name,
        slug=data.slug,
        is_active=False,
    )
    db.add(restaurant)

    try:
        db.commit()
        db.refresh(restaurant)
        return restaurant
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not create restaurant; its slug may already exist",
        )


@router.put(
    "/{restaurant_id}/owner",
    response_model=RestaurantResponse,
)
def assign_restaurant_owner(
    restaurant_id: int,
    data: RestaurantOwnerAssign,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    user = db.query(User).filter(User.id == data.user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role in (UserRole.platform_admin, UserRole.delivery_person):
        raise HTTPException(
            status_code=400,
            detail="This user cannot be assigned as a restaurant owner",
        )

    existing_owner = db.query(RestaurantMembership).filter(
        RestaurantMembership.restaurant_id == restaurant.id,
        RestaurantMembership.role == "owner",
    ).first()

    if existing_owner and existing_owner.user_id != user.id:
        raise HTTPException(
            status_code=409,
            detail="This restaurant already has an owner",
        )

    membership = db.query(RestaurantMembership).filter(
        RestaurantMembership.restaurant_id == restaurant.id,
        RestaurantMembership.user_id == user.id,
    ).first()

    try:
        if membership:
            membership.role = "owner"
        else:
            db.add(
                RestaurantMembership(
                    restaurant_id=restaurant.id,
                    user_id=user.id,
                    role="owner",
                )
            )

        # Existing order authorization also checks this global role.
        user.role = UserRole.restaurant_owner

        db.commit()
        db.refresh(restaurant)
        return restaurant
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not assign this owner",
        )

@router.post(
    "/{restaurant_id}/delivery-person",
    response_model=DeliveryPersonAssignmentResponse,
    status_code=201,
)
def assign_delivery_person(
    restaurant_id: int,
    data: DeliveryPersonAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    owner_membership = db.query(RestaurantMembership).filter(
        RestaurantMembership.restaurant_id == restaurant.id,
        RestaurantMembership.user_id == current_user.id,
        RestaurantMembership.role == "owner",
    ).first()

    if owner_membership is None:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to assign a delivery person to this restaurant",
        )
    user = db.query(User).filter(User.id == data.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role in (
        UserRole.platform_admin,
        UserRole.restaurant_owner,
    ):
        raise HTTPException(
            status_code=400,
            detail="This user cannot be assigned as a delivery person",
        )

    existing_membership = db.query(RestaurantMembership).filter(
        RestaurantMembership.restaurant_id == restaurant.id,
        RestaurantMembership.user_id == user.id,
    ).first()

    if existing_membership is not None:
        if existing_membership.role == "delivery_person":
            raise HTTPException(
                status_code=409,
                detail="This user is already assigned as a delivery person for this restaurant",
            )
        raise HTTPException(
            status_code=409,
            detail="This user is already assigned to this restaurant with a different role",
        )

    try:
        db.add(
            RestaurantMembership(
                restaurant_id=restaurant.id,
                user_id=user.id,
                role="delivery_person",
            )
        )

        user.role = UserRole.delivery_person

        db.commit()
        db.refresh(user)

        return {
            "message": "Delivery person assigned successfully",
            "user_id": user.id,
            "restaurant_id": restaurant.id,
            "role": user.role.value,
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not assign this delivery person",
        )


@router.patch(
    "/{restaurant_id}/activation",
    response_model=RestaurantResponse,
)
def set_restaurant_activation(
    restaurant_id: int,
    data: RestaurantActivationUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    restaurant.is_active = data.is_active
    db.commit()
    db.refresh(restaurant)
    return restaurant
