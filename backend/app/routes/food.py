from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.food import Food
from app.models.user import User
from app.schemas.food import FoodCreate, FoodResponse, FoodUpdate
from app.services.food import(create_food as create_food_service, 
                              get_foods as get_foods_service, 
                              get_food as get_food_service, 
                              update_food as update_food_service, 
                              delete_food as delete_food_service)
from app.routes.dependencies import get_current_user, require_role

router = APIRouter(
    prefix="/foods",
    tags=["foods"]
)

@router.post("/", response_model=FoodResponse)
def create_food(food: FoodCreate, db:Session = Depends(get_db), current_user: User = Depends(require_role("restaurant_owner"))):
    new_food = create_food_service(db, food)
    try:
        db.commit()
        db.refresh(new_food)
    except SQLAlchemyError:
        db.rollback()
        raise 
    return new_food

@router.get("/", response_model=list[FoodResponse])
def get_foods(db:Session = Depends(get_db)):
    return get_foods_service(db)

@router.get("/{food_id}", response_model=FoodResponse)
def get_food(food_id: int, db:Session = Depends(get_db)):
    food = get_food_service(db, food_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Food not found")
    return food

@router.patch("/{food_id}", response_model=FoodResponse)
def update_food(
    food_id: int,
    food: FoodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("restaurant_owner"))
):
    updated_food = update_food_service(db, food_id, food)

    if updated_food is None:
        raise HTTPException(status_code=404, detail="Food not found")

    try:
        db.commit()
        db.refresh(updated_food)
        return updated_food
    except SQLAlchemyError:
        db.rollback()
        raise
@router.delete("/{food_id}")
def delete_food(food_id: int, db:Session = Depends(get_db), current_user: User = Depends(require_role("restaurant_owner"))):
    result = delete_food_service(db, food_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Food not found")
    
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return {"message": "Food deleted successfully"}