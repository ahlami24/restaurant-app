from pydantic import BaseModel, Field

class FoodCreate(BaseModel):
    name: str 
    price: float = Field(..., gt=0)
    category: str | None = None

class FoodResponse(BaseModel):
    id: int
    name: str
    price: float
    category: str | None = None

class FoodUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(default=None, gt=0)
    category: str | None = None