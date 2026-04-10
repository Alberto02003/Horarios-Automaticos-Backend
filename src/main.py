import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.core.config import settings
from src.core.logging import logger
from src.core.rate_limit import limiter
from src.routes.auth import router as auth_router
from src.routes.members import router as members_router
from src.routes.shift_types import router as shift_types_router
from src.routes.preferences import router as preferences_router
from src.routes.schedule_periods import router as periods_router
from src.routes.assignments import router as assignments_router
from src.routes.generation import router as generation_router
from src.routes.export import router as export_router
import src.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Horarios Automaticos API started (log_level=%s)", settings.LOG_LEVEL)
    yield
    logger.info("Shutting down")


app = FastAPI(title="Horarios Automaticos API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    if request.url.path != "/health":
        logger.info("%s %s → %s (%dms)", request.method, request.url.path, response.status_code, duration)
    return response


app.include_router(auth_router)
app.include_router(members_router)
app.include_router(shift_types_router)
app.include_router(preferences_router)
app.include_router(periods_router)
app.include_router(assignments_router)
app.include_router(generation_router)
app.include_router(export_router)

# Serve uploaded files
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Horarios Automaticos API running"}
