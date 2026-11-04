from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )
    user = relationship(
        "User",
        back_populates="customer",
        uselist=False,
    )
    orders = relationship(
        "Order",
        back_populates="customer",
    )

    @property
    def name(self):
        return self.user.name

    @property
    def phone(self):
        return self.user.phone