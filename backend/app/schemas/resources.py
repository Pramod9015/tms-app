"""
Pydantic schemas for Bank, Beneficiary, and Transaction resources.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from app.models.transaction import TransactionType, AppUsed, TransactionStatus


# ─── Bank ─────────────────────────────────────────────────────────────────────

class BankCreate(BaseModel):
    bank_name: str

class BankUpdate(BaseModel):
    bank_name: str

class BankResponse(BaseModel):
    id: int
    bank_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Beneficiary ──────────────────────────────────────────────────────────────

class BeneficiaryCreate(BaseModel):
    name: str
    mobile_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None   # optional

class BeneficiaryUpdate(BaseModel):
    name: Optional[str] = None
    mobile_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None

class BeneficiaryResponse(BaseModel):
    id: int
    name: str
    mobile_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Transaction ──────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    bank_id: Optional[int] = None
    beneficiary_id: Optional[int] = None
    amount: Decimal
    transaction_type: TransactionType
    app_used: AppUsed = AppUsed.other
    status: TransactionStatus = TransactionStatus.completed
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    transaction_date: Optional[datetime] = None

class TransactionUpdate(BaseModel):
    bank_id: Optional[int] = None
    beneficiary_id: Optional[int] = None
    amount: Optional[Decimal] = None
    transaction_type: Optional[TransactionType] = None
    app_used: Optional[AppUsed] = None
    status: Optional[TransactionStatus] = None
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    transaction_date: Optional[datetime] = None

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    bank_id: Optional[int] = None
    beneficiary_id: Optional[int] = None
    amount: Decimal
    transaction_type: TransactionType
    app_used: AppUsed
    status: TransactionStatus
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    transaction_date: datetime
    created_at: datetime
    # Joined fields
    bank_name: Optional[str] = None
    beneficiary_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource: str
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
