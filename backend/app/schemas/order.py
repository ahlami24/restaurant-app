from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderItemCreate(BaseModel):
    food_id: int
    quantity: int = Field(..., gt=0)

class OrderItemResponse(BaseModel):
    food_id: int
    quantity: int
    price: float
    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    address: str
    order_items: list[OrderItemCreate] = Field(min_length=1)  # List of dictionaries containing food_id and quantity

class OrderResponse(BaseModel):
    id: int
    customer_id: int
    address: str
    total_price: float
    status: OrderStatus
    order_items: list[OrderItemResponse]  # List of dictionaries containing food_id, quantity, and price
    model_config = ConfigDict(from_attributes=True)

class OrderItemUpdate(BaseModel):
    food_id: int
    quantity: int = Field(..., gt=0)
