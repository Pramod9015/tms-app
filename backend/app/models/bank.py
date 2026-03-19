"""
Bank ORM model — simple name registry only.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Bank(Base):
    __tablename__ = "banks"
    __table_args__ = (
        UniqueConstraint("user_id", "bank_name", name="uq_user_bank_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bank_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates=None)
    transactions = relationship("Transaction", back_populates="bank", cascade="all, delete")
