import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RestaurantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=80)

    @field_validator("name", "slug", mode="before")
    @classmethod
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value):
        value = value.lower()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise ValueError(
                "Slug must contain lowercase letters, numbers, and single hyphens"
            )
        return value


class RestaurantOwnerAssign(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int = Field(gt=0)

class DeliveryPersonAssign(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int = Field(gt=0)

class DeliveryPersonAssignmentResponse(BaseModel):
    message: str
    user_id: int
    restaurant_id: int
    role: str


class RestaurantActivationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool


class RestaurantResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
