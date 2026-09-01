import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.envelope import fail
from app.routers.patients import router as patients_router
from app.routers.stats import router as stats_router
from app.routers.vapi import router as vapi_router
from app.seed import seed_patients

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("voice-agent")
settings = get_settings()
ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
SKIP_LIFESPAN = os.getenv("SKIP_LIFESPAN") == "1"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seeded = seed_patients(db)
        if seeded:
            logger.info("Seeded %s demo patients", seeded)
    finally:
        db.close()
    logger.info("API ready on %s", settings.public_base_url)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=None if SKIP_LIFESPAN else lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_error_handler(_, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, list):
        detail = "; ".join(str(item) for item in detail)
    return fail(str(detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, exc: RequestValidationError):
    messages = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", []) if part != "body")
        messages.append(f"{loc}: {err.get('msg')}" if loc else str(err.get("msg")))
    return fail("; ".join(messages) or "Invalid request", 422, "validation_error")


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("UNHANDLED %s %s", request.method, request.url.path)
    return fail("An unexpected server error occurred", 500, "server_error")


@app.get("/health")
def health():
    return {"data": {"status": "ok", "service": settings.app_name}, "error": None}


@app.get("/meta")
def meta():
    return {
        "data": {
            "service": settings.app_name,
            "phone_number": settings.vapi_phone_number or "+18604108127",
            "public_base_url": settings.public_base_url,
            "dashboard": "/",
            "api_docs": "/docs",
        },
        "error": None,
    }


app.include_router(patients_router)
app.include_router(stats_router)
app.include_router(vapi_router)

if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def dashboard():
    return FileResponse(FRONTEND / "index.html")


if SKIP_LIFESPAN:
    Base.metadata.create_all(bind=engine)
    _db = SessionLocal()
    try:
        seed_patients(_db)
    finally:
        _db.close()
