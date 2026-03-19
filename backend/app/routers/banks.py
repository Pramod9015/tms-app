"""
Banks router — name registry only (no account number / IFSC / branch).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List
from app.database import get_db
from app.models.bank import Bank
from app.models.user import User
from app.schemas.resources import BankCreate, BankUpdate, BankResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/banks", tags=["Banks"])


@router.get("", response_model=List[BankResponse])
async def list_banks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Bank).where(Bank.user_id == current_user.id).order_by(Bank.bank_name)
    )
    return result.scalars().all()


@router.post("", response_model=BankResponse, status_code=201)
async def create_bank(
    data: BankCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = data.bank_name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Bank name cannot be empty")
    bank = Bank(user_id=current_user.id, bank_name=name)
    db.add(bank)
    try:
        await db.flush()
        await db.refresh(bank)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Bank '{name}' already exists")
    return bank


@router.get("/{bank_id}", response_model=BankResponse)
async def get_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Bank).where(Bank.id == bank_id, Bank.user_id == current_user.id)
    )
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    return bank


@router.put("/{bank_id}", response_model=BankResponse)
async def update_bank(
    bank_id: int,
    data: BankUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Bank).where(Bank.id == bank_id, Bank.user_id == current_user.id)
    )
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    new_name = data.bank_name.strip()
    if not new_name:
        raise HTTPException(status_code=422, detail="Bank name cannot be empty")
    bank.bank_name = new_name
    try:
        await db.flush()
        await db.refresh(bank)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Bank '{new_name}' already exists")
    return bank


@router.delete("/{bank_id}", status_code=204)
async def delete_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Bank).where(Bank.id == bank_id, Bank.user_id == current_user.id)
    )
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    await db.delete(bank)
    await db.flush()
