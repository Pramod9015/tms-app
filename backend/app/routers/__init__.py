from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.banks import router as banks_router
from app.routers.beneficiaries import router as beneficiaries_router
from app.routers.transactions import router as transactions_router
from app.routers.dashboard import router as dashboard_router
from app.routers.reports import router as reports_router
from app.routers.audit import router as audit_router

__all__ = [
    "auth_router", "users_router", "banks_router", "beneficiaries_router",
    "transactions_router", "dashboard_router", "reports_router", "audit_router",
]
