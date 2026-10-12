from pydantic import BaseModel, ConfigDict, Field

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)

class CustomerResponse(BaseModel):
    id: int
    name: str
    phone: str 
    model_config = ConfigDict(from_attributes=True)

class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    phone: str | None = Field(default=None, min_length=1)