from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
from sqlalchemy.orm import relationship

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    orders = relationship("Order", back_populates="customer")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    user = relationship("User", back_populates="customer", uselist=False)