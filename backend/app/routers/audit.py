"""
Audit logs router — Admin-only view of system activity.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.resources import AuditLogResponse
from app.dependencies import require_admin

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
    limit: int = Query(200, le=1000),
    offset: int = Query(0),
):
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
