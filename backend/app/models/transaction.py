"""
Transaction ORM model.
notes field is AES-256 encrypted.
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class TransactionType(str, enum.Enum):
    withdrawal = "withdrawal"
    transfer = "transfer"
    deposit = "deposit"
    payment = "payment"


class AppUsed(str, enum.Enum):
    phonepe = "PhonePe"
    paytm = "Paytm"
    paynear = "PayNear"
    bank_app = "Bank App"
    atm = "ATM"
    upi = "UPI"
    cash = "Cash"
    other = "Other"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    reversed = "reversed"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="SET NULL"), nullable=True)
    beneficiary_id = Column(Integer, ForeignKey("beneficiaries.id", ondelete="SET NULL"), nullable=True)

    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    app_used = Column(Enum(AppUsed), default=AppUsed.other, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.completed, nullable=False)

    # Encrypted fields
    notes_enc = Column(Text, nullable=True)  # Encrypted notes

    # Reference number (non-sensitive)
    reference_number = Column(String(100), nullable=True)

    transaction_date = Column(DateTime(timezone=True), nullable=False,
                              default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates=None)
    bank = relationship("Bank", back_populates="transactions")
    beneficiary = relationship("Beneficiary", back_populates="transactions")
