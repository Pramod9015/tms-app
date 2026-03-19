"""
Dashboard analytics router.
Provides summary cards and chart data for the frontend.
"""
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models.transaction import Transaction, TransactionType, AppUsed
from app.models.bank import Bank
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Summary cards: total transactions, withdrawals, transfers, today/month amounts."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    base_q = select(Transaction).where(Transaction.user_id == current_user.id)

    # Total counts
    total_result = await db.execute(base_q)
    all_txns = total_result.scalars().all()

    total = len(all_txns)
    withdrawals = sum(1 for t in all_txns if t.transaction_type == TransactionType.withdrawal)
    transfers = sum(1 for t in all_txns if t.transaction_type == TransactionType.transfer)
    total_amount = sum(float(t.amount) for t in all_txns)

    today_txns = [t for t in all_txns if t.transaction_date >= today_start]
    today_amount = sum(float(t.amount) for t in today_txns)
    today_count = len(today_txns)

    month_txns = [t for t in all_txns if t.transaction_date >= month_start]
    month_amount = sum(float(t.amount) for t in month_txns)
    month_count = len(month_txns)

    return {
        "total_transactions": total,
        "total_withdrawals": withdrawals,
        "total_transfers": transfers,
        "total_amount": round(total_amount, 2),
        "today_transactions": today_count,
        "today_amount": round(today_amount, 2),
        "month_transactions": month_count,
        "month_amount": round(month_amount, 2),
    }


@router.get("/daily-chart")
async def get_daily_chart(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily transaction amounts for the last N days (line chart)."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= since,
        )
    )
    transactions = result.scalars().all()

    daily = defaultdict(float)
    for t in transactions:
        day_key = t.transaction_date.strftime("%Y-%m-%d")
        daily[day_key] += float(t.amount)

    # Fill in missing days
    chart_data = []
    for i in range(days):
        d = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        chart_data.append({"date": d, "amount": round(daily.get(d, 0), 2)})

    return chart_data


@router.get("/app-usage")
async def get_app_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """App-wise transaction count (pie chart)."""
    result = await db.execute(
        select(Transaction).where(Transaction.user_id == current_user.id)
    )
    transactions = result.scalars().all()

    counts = defaultdict(int)
    for t in transactions:
        counts[t.app_used.value] += 1

    return [{"app": k, "count": v} for k, v in counts.items()]


@router.get("/bank-wise")
async def get_bank_wise(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bank-wise transaction amounts (bar chart)."""
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.bank_id.isnot(None),
        )
    )
    transactions = result.scalars().all()

    bank_cache = {}
    bank_amounts = defaultdict(float)
    bank_counts = defaultdict(int)

    for t in transactions:
        if t.bank_id not in bank_cache:
            r = await db.execute(select(Bank).where(Bank.id == t.bank_id))
            b = r.scalar_one_or_none()
            bank_cache[t.bank_id] = b.bank_name if b else f"Bank {t.bank_id}"
        name = bank_cache[t.bank_id]
        bank_amounts[name] += float(t.amount)
        bank_counts[name] += 1

    return [
        {"bank": k, "amount": round(bank_amounts[k], 2), "count": bank_counts[k]}
        for k in bank_amounts
    ]


@router.get("/monthly-trend")
async def get_monthly_trend(
    months: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly spending trend (line chart)."""
    since = datetime.now(timezone.utc).replace(day=1) - timedelta(days=30 * months)
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= since,
        )
    )
    transactions = result.scalars().all()

    monthly = defaultdict(float)
    for t in transactions:
        key = t.transaction_date.strftime("%Y-%m")
        monthly[key] += float(t.amount)

    return [{"month": k, "amount": round(v, 2)} for k, v in sorted(monthly.items())]


@router.get("/recent-transactions")
async def get_recent_transactions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recent transactions for the dashboard table."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.transaction_date.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    items = []
    for t in transactions:
        bank_name, ben_name = None, None
        if t.bank_id:
            r = await db.execute(select(Bank).where(Bank.id == t.bank_id))
            b = r.scalar_one_or_none()
            bank_name = b.bank_name if b else None
        items.append({
            "id": t.id,
            "date": t.transaction_date.isoformat(),
            "amount": float(t.amount),
            "transaction_type": t.transaction_type.value,
            "app_used": t.app_used.value,
            "status": t.status.value,
            "bank_name": bank_name,
            "reference_number": t.reference_number,
        })
    return items
