from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.restaurant import RestaurantResponse
from app.services.restaurant import (
    get_restaurants as get_restaurants_service,
    get_restaurant_by_slug as get_restaurant_by_slug_service,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=list[RestaurantResponse])
def get_restaurants(db: Session = Depends(get_db)):
    return get_restaurants_service(db)


@router.get("/{restaurant_slug}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_slug: str,
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant_by_slug_service(db, restaurant_slug)

    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return restaurant
