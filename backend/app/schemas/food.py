from pydantic import BaseModel, Field

class FoodCreate(BaseModel):
    name: str 
    price: float = Field(..., gt=0)

class FoodResponse(BaseModel):
    id: int
    name: str
    price: float

class FoodUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(default=None, gt=0)