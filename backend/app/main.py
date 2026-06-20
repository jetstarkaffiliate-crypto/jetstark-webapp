import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from app.config import settings
from app.database import init_db
from app.api import auth, users, products, orders, affiliates, payouts, reviews, payments, cart, wishlist, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment="production" if not settings.debug else "development",
            traces_sample_rate=0.1,
        )
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logger = logging.getLogger(__name__)
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )

# Health check
@app.get("/api/health")
async def health_check():
    from app.database import async_session_factory
    try:
        async with async_session_factory() as session:
            await session.execute(select(1))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "version": "1.0.0", "app": settings.app_name, "database": db_ok}

# Public config (no auth required)
@app.get("/api/config")
async def public_config():
    return {
        "paystack_public_key": settings.paystack_public_key,
        "app_name": settings.app_name,
    }

# Uploads directory (Render disk or local)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
UPLOAD_PATH = Path(UPLOAD_DIR) / "products"
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_PATH.parent)), name="uploads")

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(affiliates.router)
app.include_router(payouts.router)
app.include_router(reviews.router)
app.include_router(payments.router)
app.include_router(cart.router)
app.include_router(wishlist.router)
app.include_router(admin.router)

# Serve frontend static files (for Render single-service deployment).
# MUST be registered after API routes so API takes precedence over catch-all.
FRONTEND_DIR = None
for candidate in [
    Path(__file__).parent.parent / "frontend",          # Docker (/app/frontend)
    Path(__file__).parent.parent.parent / "frontend",   # Local dev (repo-root/frontend)
]:
    if candidate.is_dir():
        FRONTEND_DIR = candidate
        break
if FRONTEND_DIR:
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        index = FRONTEND_DIR / "index.html"
        if index.is_file():
            return FileResponse(str(index))
        return JSONResponse(status_code=404, content={"detail": "Not found"})
