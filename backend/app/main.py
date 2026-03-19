"""
FastAPI Application entry point.
Registers all routers, CORS, rate limiting, and startup events.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db
from app.routers import auth, users, banks, beneficiaries, transactions, dashboard, reports, audit
from app.routers import banks_import, slip_ocr

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup/shutdown tasks."""
    logger.info("🚀 TMS Backend starting — initializing database...")
    await init_db()
    await _bootstrap_admin()
    logger.info("✅ Database ready.")
    yield
    logger.info("🛑 TMS Backend shutting down.")


async def _bootstrap_admin():
    """Create default admin user on first run if not present."""
    from app.database import AsyncSessionLocal
    from app.models.user import User, UserRole
    from app.security.hashing import hash_password
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        if result.scalar_one_or_none() is None:
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.admin,
            )
            db.add(admin)
            await db.commit()
            logger.info(f"✅ Default admin user '{settings.ADMIN_USERNAME}' created.")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Secure Transaction Management System — End-to-End Encrypted Financial Records",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(banks_import.router)   # must be before banks to avoid {bank_id} conflict
app.include_router(banks.router)
app.include_router(beneficiaries.router)
app.include_router(slip_ocr.router)        # must be before transactions to avoid {id} conflict
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(audit.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
