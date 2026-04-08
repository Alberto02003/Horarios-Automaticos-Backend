from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.routes.auth import router as auth_router
from src.routes.members import router as members_router
from src.routes.shift_types import router as shift_types_router
from src.routes.preferences import router as preferences_router
from src.routes.schedule_periods import router as periods_router
from src.routes.assignments import router as assignments_router
from src.routes.generation import router as generation_router
import src.models  # noqa: F401 — register models with SQLAlchemy metadata

app = FastAPI(title="Horarios Automaticos API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(members_router)
app.include_router(shift_types_router)
app.include_router(preferences_router)
app.include_router(periods_router)
app.include_router(assignments_router)
app.include_router(generation_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Horarios Automaticos API running"}
