"""
Audit Log ORM model — tracks every important action.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)      # e.g. CREATE, UPDATE, DELETE, LOGIN
    resource = Column(String(50), nullable=False)    # e.g. transaction, user, bank
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)      # JSON string for extra context
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
