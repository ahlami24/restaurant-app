from sqlalchemy import (
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.food import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    memberships = relationship(
        "RestaurantMembership", back_populates="restaurant"
    )
    foods = relationship("Food", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")


class RestaurantMembership(Base):
    __tablename__ = "restaurant_memberships"

    __table_args__ = (
        UniqueConstraint(
            "user_id", "restaurant_id",
            name="uq_user_restaurant_membership",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    restaurant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("restaurants.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)

    user = relationship("User", back_populates="restaurant_memberships")
    restaurant = relationship("Restaurant", back_populates="memberships")
   