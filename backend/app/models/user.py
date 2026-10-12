from sqlalchemy import Integer, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.food import Base
from enum import Enum


class UserRole(str, Enum):
    customer = "customer"
    restaurant_owner = "restaurant_owner"
    delivery_person = "delivery_person"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer = relationship("Customer", back_populates="user", uselist=False)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole), nullable=False)