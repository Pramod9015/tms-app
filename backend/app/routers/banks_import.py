"""
Banks import router — bulk import from JSON list, TXT file upload, or Excel upload.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import List
import io

from app.database import get_db
from app.models.bank import Bank
from app.models.user import User
from app.dependencies import get_current_user
from app.data.bank_list import BANK_LIST

router = APIRouter(prefix="/api/banks", tags=["Banks"])


class ImportResult(BaseModel):
    added: int
    skipped: int
    total: int
    added_names: List[str]
    skipped_names: List[str]


class BulkImportRequest(BaseModel):
    bank_names: List[str]


async def _bulk_insert(
    names: List[str],
    user_id: int,
    db: AsyncSession,
) -> ImportResult:
    """Insert unique, non-empty bank names. Skip duplicates gracefully."""
    # Fetch names already in DB for this user
    existing_result = await db.execute(
        select(Bank.bank_name).where(Bank.user_id == user_id)
    )
    existing = {row[0].lower() for row in existing_result.all()}

    added, skipped = [], []
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        if name.lower() in existing:
            skipped.append(name)
        else:
            db.add(Bank(user_id=user_id, bank_name=name))
            existing.add(name.lower())
            added.append(name)

    if added:
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="Duplicate bank detected during bulk insert")

    return ImportResult(
        added=len(added),
        skipped=len(skipped),
        total=len(added) + len(skipped),
        added_names=added,
        skipped_names=skipped,
    )


@router.get("/defaults", response_model=List[str])
async def get_default_bank_list():
    """Return the built-in list of Indian banks for preview/selection."""
    return BANK_LIST


@router.post("/import/defaults", response_model=ImportResult)
async def import_default_banks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add all banks from the built-in Indian bank list."""
    return await _bulk_insert(BANK_LIST, current_user.id, db)


@router.post("/import/list", response_model=ImportResult)
async def import_bank_list(
    data: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add banks from a JSON array of names (selected from the default list)."""
    return await _bulk_insert(data.bank_names, current_user.id, db)


@router.post("/import/txt", response_model=ImportResult)
async def import_banks_txt(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a plain-text file with one bank name per line.
    Accepts .txt or .csv files (comma- or newline-separated).
    """
    if not file.filename.lower().endswith((".txt", ".csv")):
        raise HTTPException(status_code=415, detail="Only .txt or .csv files are accepted")
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # Support both newline-separated and comma-separated formats
    if "," in text and "\n" not in text.strip():
        names = [n.strip() for n in text.split(",")]
    else:
        names = [line.strip() for line in text.splitlines()]

    names = [n for n in names if n]
    return await _bulk_insert(names, current_user.id, db)


@router.post("/import/excel", response_model=ImportResult)
async def import_banks_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an Excel file (.xlsx or .xls).
    Reads the first column of every sheet for bank names.
    """
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=415, detail="Only .xlsx or .xls files are accepted")
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl not installed")

    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read Excel file: {e}")

    names = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cell = row[0] if row else None
            if cell and str(cell).strip():
                names.append(str(cell).strip())
    wb.close()

    return await _bulk_insert(names, current_user.id, db)
