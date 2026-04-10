from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.models.user import User
from src.schemas.schedule_period import PeriodCreate, PeriodResponse
from src.schemas.pagination import PaginatedResponse, PaginationParams
from src.services import schedule_period_service

router = APIRouter(prefix="/api/schedule-periods", tags=["schedule-periods"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PaginatedResponse[PeriodResponse])
async def list_periods(pagination: PaginationParams = Depends(), db: AsyncSession = Depends(get_db)):
    items, total = await schedule_period_service.list_periods(db, pagination.offset, pagination.page_size)
    return PaginatedResponse(items=items, total=total, page=pagination.page, page_size=pagination.page_size, pages=max(1, (total + pagination.page_size - 1) // pagination.page_size))


@router.get("/{period_id}", response_model=PeriodResponse)
async def get_period(period_id: int, db: AsyncSession = Depends(get_db)):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")
    return schedule_period_service._to_dict(period)


@router.post("", response_model=PeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_period(body: PeriodCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return await schedule_period_service.create_period(db, body, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{period_id}/activate", response_model=PeriodResponse)
async def activate_period(period_id: int, db: AsyncSession = Depends(get_db)):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")
    if period.status == "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El periodo ya esta activo")
    try:
        return await schedule_period_service.activate_period(db, period)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{period_id}", response_model=PeriodResponse)
async def delete_period(period_id: int, db: AsyncSession = Depends(get_db)):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")
    return await schedule_period_service.delete_period(db, period)
