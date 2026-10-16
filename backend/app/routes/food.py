from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.food import Food
from app.models.restaurant import Restaurant, RestaurantMembership
from app.models.user import User
from app.schemas.food import FoodCreate, FoodResponse, FoodUpdate
from app.services.food import(create_food as create_food_service, 
                              get_foods as get_foods_service, 
                              get_food as get_food_service, 
                              update_food as update_food_service, 
                              delete_food as delete_food_service)
from app.routes.dependencies import get_current_user, require_role, get_restaurant_membership

router = APIRouter(tags=["foods"])

@router.get("/restaurants/{restaurant_slug}/foods", response_model=list[FoodResponse])
def get_restaurant_foods(
    restaurant_slug: str,
    db: Session = Depends(get_db)
):
    restaurant = db.query(Restaurant).filter(Restaurant.slug == restaurant_slug, Restaurant.is_active == True).first()
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return get_foods_service(db, restaurant.id)

@router.get("/restaurants/{restaurant_slug}/foods/{food_id}", response_model=FoodResponse)
def get_food(
    restaurant_slug: str,
    food_id: int,
    db:Session = Depends(get_db)
):
    restaurant = db.query(Restaurant).filter(Restaurant.slug == restaurant_slug, Restaurant.is_active == True, ).first()
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    food = get_food_service(db, food_id, restaurant.id)
    if food is None:
        raise HTTPException(status_code=404, detail="Food not found")
    return food


@router.post("/restaurants/{restaurant_slug}/foods", response_model=FoodResponse)
def create_food_for_restaurant(
    restaurant_slug: str,
    food: FoodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: RestaurantMembership = Depends(get_restaurant_membership)
):

    if membership.role not in ("owner", "manager"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource",
        )

    new_food = create_food_service(db, food, restaurant_id=membership.restaurant_id)
    try:
        db.commit()
        db.refresh(new_food)
    except SQLAlchemyError:
        db.rollback()
        raise
    return new_food

@router.patch("/restaurants/{restaurant_slug}/foods/{food_id}", response_model=FoodResponse)
def update_food_for_restaurant(
    restaurant_slug: str,
    food_id: int,
    food: FoodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: RestaurantMembership = Depends(get_restaurant_membership)
):
    if membership.role not in ("owner", "manager"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource",
        )

    updated_food = update_food_service(db, food_id, food, restaurant_id=membership.restaurant_id)

    if updated_food is None:
        raise HTTPException(status_code=404, detail="Food not found")

    try:
        db.commit()
        db.refresh(updated_food)
        return updated_food
    except SQLAlchemyError:
        db.rollback()
        raise

@router.delete("/restaurants/{restaurant_slug}/foods/{food_id}")
def delete_food_for_restaurant(
    restaurant_slug: str,
    food_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: RestaurantMembership = Depends(get_restaurant_membership)
):
    if membership.role not in ("owner", "manager"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resource",
        )

    result = delete_food_service(db, food_id, restaurant_id=membership.restaurant_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Food not found")

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return {"message": "Food deleted successfully"}