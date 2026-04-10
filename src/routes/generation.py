from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.rate_limit import limiter
from src.core.deps import get_current_user
from src.models.user import User
from src.schemas.generation import GenerationRequest, GenerationResponse, GenerationRunResponse
from src.services.generator import engine
from src.services import schedule_period_service

router = APIRouter(prefix="/api/schedule-periods/{period_id}", tags=["generation"], dependencies=[Depends(get_current_user)])


@router.post("/generate", response_model=GenerationResponse)
@limiter.limit("5/minute")
async def generate(
    request: Request,
    period_id: int,
    body: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")
    if period.status == "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede generar en un periodo activo")

    try:
        result = await engine.run_generation(db, period_id, user.id, body.strategy, body.fill_unassigned_only)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return result


@router.get("/generation-runs", response_model=list[GenerationRunResponse])
async def list_runs(period_id: int, db: AsyncSession = Depends(get_db)):
    return await engine.list_generation_runs(db, period_id)
