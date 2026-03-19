"""
Beneficiary ORM model.
All sensitive fields (name, mobile, customer_id, account_number) are AES-256 encrypted.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String
from sqlalchemy.orm import relationship
from app.database import Base


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name_enc = Column(Text, nullable=False)             # Encrypted: beneficiary name
    mobile_enc = Column(Text, nullable=True)            # Encrypted: mobile number
    customer_id_enc = Column(Text, nullable=True)       # Encrypted: customer ID
    bank_name = Column(String(100), nullable=True)      # Non-sensitive
    account_number_enc = Column(Text, nullable=True)    # Encrypted: account number
    ifsc_code = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates=None)
    transactions = relationship("Transaction", back_populates="beneficiary")
