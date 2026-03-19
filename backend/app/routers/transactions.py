"""
Transactions router — CRUD with search/filter and AES-256 notes encryption.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.transaction import Transaction
from app.models.bank import Bank
from app.models.beneficiary import Beneficiary
from app.models.user import User
from app.schemas.resources import TransactionCreate, TransactionUpdate, TransactionResponse
from app.security.encryption import encrypt_field, decrypt_field
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


def _to_response(t: Transaction, bank: Optional[Bank] = None, ben: Optional[Beneficiary] = None) -> TransactionResponse:
    return TransactionResponse(
        id=t.id,
        user_id=t.user_id,
        bank_id=t.bank_id,
        beneficiary_id=t.beneficiary_id,
        amount=t.amount,
        transaction_type=t.transaction_type,
        app_used=t.app_used,
        status=t.status,
        notes=decrypt_field(t.notes_enc),
        reference_number=t.reference_number,
        transaction_date=t.transaction_date,
        created_at=t.created_at,
        bank_name=bank.bank_name if bank else None,
        beneficiary_name=decrypt_field(ben.name_enc) if ben else None,
    )


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: Optional[int] = Query(None),
    beneficiary_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    app_used: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    q = select(Transaction).where(Transaction.user_id == current_user.id)
    if bank_id:
        q = q.where(Transaction.bank_id == bank_id)
    if beneficiary_id:
        q = q.where(Transaction.beneficiary_id == beneficiary_id)
    if transaction_type:
        q = q.where(Transaction.transaction_type == transaction_type)
    if app_used:
        q = q.where(Transaction.app_used == app_used)
    if date_from:
        q = q.where(Transaction.transaction_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        q = q.where(Transaction.transaction_date <= datetime.combine(date_to, datetime.max.time()))
    q = q.order_by(Transaction.transaction_date.desc()).limit(limit).offset(offset)

    result = await db.execute(q)
    transactions = result.scalars().all()

    # Fetch related banks and beneficiaries
    responses = []
    for t in transactions:
        bank = None
        ben = None
        if t.bank_id:
            r = await db.execute(select(Bank).where(Bank.id == t.bank_id))
            bank = r.scalar_one_or_none()
        if t.beneficiary_id:
            r = await db.execute(select(Beneficiary).where(Beneficiary.id == t.beneficiary_id))
            ben = r.scalar_one_or_none()
        responses.append(_to_response(t, bank, ben))
    return responses


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    txn_date = data.transaction_date or datetime.utcnow()
    txn = Transaction(
        user_id=current_user.id,
        bank_id=data.bank_id,
        beneficiary_id=data.beneficiary_id,
        amount=data.amount,
        transaction_type=data.transaction_type,
        app_used=data.app_used,
        status=data.status,
        notes_enc=encrypt_field(data.notes),
        reference_number=data.reference_number,
        transaction_date=txn_date,
    )
    db.add(txn)
    await db.flush()
    await db.refresh(txn)

    bank, ben = None, None
    if txn.bank_id:
        r = await db.execute(select(Bank).where(Bank.id == txn.bank_id))
        bank = r.scalar_one_or_none()
    if txn.beneficiary_id:
        r = await db.execute(select(Beneficiary).where(Beneficiary.id == txn.beneficiary_id))
        ben = r.scalar_one_or_none()
    return _to_response(txn, bank, ben)


@router.get("/{txn_id}", response_model=TransactionResponse)
async def get_transaction(
    txn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == txn_id, Transaction.user_id == current_user.id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_response(txn)


@router.put("/{txn_id}", response_model=TransactionResponse)
async def update_transaction(
    txn_id: int,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == txn_id, Transaction.user_id == current_user.id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if data.bank_id is not None: txn.bank_id = data.bank_id
    if data.beneficiary_id is not None: txn.beneficiary_id = data.beneficiary_id
    if data.amount is not None: txn.amount = data.amount
    if data.transaction_type is not None: txn.transaction_type = data.transaction_type
    if data.app_used is not None: txn.app_used = data.app_used
    if data.status is not None: txn.status = data.status
    if data.notes is not None: txn.notes_enc = encrypt_field(data.notes)
    if data.reference_number is not None: txn.reference_number = data.reference_number
    if data.transaction_date is not None: txn.transaction_date = data.transaction_date
    await db.flush()
    await db.refresh(txn)
    return _to_response(txn)


@router.delete("/{txn_id}", status_code=204)
async def delete_transaction(
    txn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == txn_id, Transaction.user_id == current_user.id)
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await db.delete(txn)
