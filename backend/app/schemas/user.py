from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)

from app.models.user import UserRole

class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=100)
    phone: str = Field(max_length=20)
    password: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            value = value.strip()
        if not value:
            return None
        return value.lower()



class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    role: UserRole
    email: EmailStr | None = None
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    identifier: str
    password: str

    @model_validator(mode="before")
    @classmethod
    def support_email_or_phone(cls, value):
        if isinstance(value, dict):
            value = value.copy()
            if "phone" in value and "identifier" not in value:
                value["identifier"] = value.pop("phone")
        return value
