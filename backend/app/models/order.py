from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    customer = relationship("Customer", back_populates="orders")

    restaurant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("restaurants.id"), nullable=False
    )
    restaurant = relationship("Restaurant", back_populates="orders")

    delivery_person_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("delivery_persons.id"),
        nullable=True,
    )
    delivery_person = relationship(
        "DeliveryPerson",
        back_populates="orders",
    )

    address: Mapped[str] = mapped_column(String, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)

    order_items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
