"""
Beneficiaries router — CRUD + mobile-number lookup for auto-fill in transactions.
Customer ID removed. IFSC is optional.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.models.beneficiary import Beneficiary
from app.models.user import User
from app.schemas.resources import BeneficiaryCreate, BeneficiaryUpdate, BeneficiaryResponse
from app.security.encryption import encrypt_field, decrypt_field
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiaries"])


def _to_response(b: Beneficiary) -> BeneficiaryResponse:
    return BeneficiaryResponse(
        id=b.id,
        name=decrypt_field(b.name_enc) or "",
        mobile_number=decrypt_field(b.mobile_enc),
        bank_name=b.bank_name,
        account_number=decrypt_field(b.account_number_enc),
        ifsc_code=b.ifsc_code,
        created_at=b.created_at,
    )


@router.get("", response_model=List[BeneficiaryResponse])
async def list_beneficiaries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Beneficiary).where(Beneficiary.user_id == current_user.id)
    )
    return [_to_response(b) for b in result.scalars().all()]


@router.get("/by-mobile", response_model=List[BeneficiaryResponse])
async def get_beneficiaries_by_mobile(
    mobile: str = Query(..., description="Mobile number to look up"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all beneficiaries whose decrypted mobile number matches.
    Used for auto-fill in the Add Transaction form.
    """
    # Fetch all beneficiaries for this user and filter after decryption
    # (mobile is encrypted at rest, so we can't do a DB-level search)
    result = await db.execute(
        select(Beneficiary).where(Beneficiary.user_id == current_user.id)
    )
    all_bens = result.scalars().all()
    matched = [
        b for b in all_bens
        if decrypt_field(b.mobile_enc) == mobile.strip()
    ]
    return [_to_response(b) for b in matched]


@router.post("", response_model=BeneficiaryResponse, status_code=201)
async def create_beneficiary(
    data: BeneficiaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    beneficiary = Beneficiary(
        user_id=current_user.id,
        name_enc=encrypt_field(data.name),
        mobile_enc=encrypt_field(data.mobile_number),
        customer_id_enc=None,   # field removed from UI
        bank_name=data.bank_name,
        account_number_enc=encrypt_field(data.account_number),
        ifsc_code=data.ifsc_code or None,
    )
    db.add(beneficiary)
    await db.flush()
    await db.refresh(beneficiary)
    return _to_response(beneficiary)


@router.get("/{ben_id}", response_model=BeneficiaryResponse)
async def get_beneficiary(
    ben_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Beneficiary).where(Beneficiary.id == ben_id, Beneficiary.user_id == current_user.id)
    )
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    return _to_response(b)


@router.put("/{ben_id}", response_model=BeneficiaryResponse)
async def update_beneficiary(
    ben_id: int,
    data: BeneficiaryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Beneficiary).where(Beneficiary.id == ben_id, Beneficiary.user_id == current_user.id)
    )
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    if data.name is not None:
        b.name_enc = encrypt_field(data.name)
    if data.mobile_number is not None:
        b.mobile_enc = encrypt_field(data.mobile_number)
    if data.bank_name is not None:
        b.bank_name = data.bank_name
    if data.account_number is not None:
        b.account_number_enc = encrypt_field(data.account_number)
    if data.ifsc_code is not None:
        b.ifsc_code = data.ifsc_code
    await db.flush()
    await db.refresh(b)
    return _to_response(b)


@router.delete("/{ben_id}", status_code=204)
async def delete_beneficiary(
    ben_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Beneficiary).where(Beneficiary.id == ben_id, Beneficiary.user_id == current_user.id)
    )
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Beneficiary not found")
    await db.delete(b)
