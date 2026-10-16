from pydantic import BaseModel, ConfigDict


class RestaurantResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
