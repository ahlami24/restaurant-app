from enum import Enum

from sqlalchemy import Integer, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, Enum):
    user = "user"
    platform_admin = "platform_admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, name="userrole"),
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    customer = relationship(
        "Customer",
        back_populates="user",
        uselist=False,
    )

    delivery_person = relationship(
        "DeliveryPerson",
        back_populates="user",
        uselist=False,
    )

    restaurant_memberships = relationship(
        "RestaurantMembership",
        back_populates="user",
    )
