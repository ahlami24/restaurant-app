from pydantic import BaseModel, Field, ConfigDict
from app.models.user import UserRole

from pydantic import BaseModel, Field, ConfigDict

class UserCreate(BaseModel):
    name: str = Field(max_length=100)
    phone: str = Field(max_length=20)
    password: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")
    
class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    role: UserRole
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    phone: str = Field(max_length=20)
    password: str = Field(min_length=1, max_length=255)