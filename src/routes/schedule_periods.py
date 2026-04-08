from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.models.user import User
from src.schemas.schedule_period import PeriodCreate, PeriodResponse
from src.services import schedule_period_service

router = APIRouter(prefix="/api/schedule-periods", tags=["schedule-periods"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[PeriodResponse])
async def list_periods(db: AsyncSession = Depends(get_db)):
    return await schedule_period_service.list_periods(db)


@router.get("/{period_id}", response_model=PeriodResponse)
async def get_period(period_id: int, db: AsyncSession = Depends(get_db)):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")
    return schedule_period_service._to_dict(period)


@router.post("", response_model=PeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_period(body: PeriodCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await schedule_period_service.create_period(db, body, user.id)


@router.patch("/{period_id}/activate", response_model=PeriodResponse)
async def activate_period(period_id: int, db: AsyncSession = Depends(get_db)):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")
    if period.status == "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El periodo ya esta activo")
    return await schedule_period_service.activate_period(db, period)


@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_period(period_id: int, db: AsyncSession = Depends(get_db)):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")
    await schedule_period_service.delete_period(db, period)
