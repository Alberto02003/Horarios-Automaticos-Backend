from datetime import date, datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schedule_period import SchedulePeriod
from src.models.schedule_assignment import ScheduleAssignment
from src.models.generation_run import GenerationRun
from src.schemas.schedule_period import PeriodCreate


async def list_periods(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(SchedulePeriod).order_by(SchedulePeriod.year.desc(), SchedulePeriod.month.desc()))
    return [_to_dict(p) for p in result.scalars().all()]


async def get_period(db: AsyncSession, period_id: int) -> SchedulePeriod | None:
    result = await db.execute(select(SchedulePeriod).where(SchedulePeriod.id == period_id))
    return result.scalar_one_or_none()


async def check_active_exists(db: AsyncSession, year: int, month: int) -> bool:
    result = await db.execute(
        select(SchedulePeriod).where(
            SchedulePeriod.year == year,
            SchedulePeriod.month == month,
            SchedulePeriod.status == "active",
        )
    )
    return result.scalar_one_or_none() is not None


async def create_period(db: AsyncSession, data: PeriodCreate, user_id: int) -> dict:
    if await check_active_exists(db, data.year, data.month):
        raise ValueError(f"Ya existe un periodo activo para {data.month}/{data.year}. Eliminalo primero.")

    period = SchedulePeriod(
        name=data.name,
        year=data.year,
        month=data.month,
        start_date=date.fromisoformat(data.start_date),
        end_date=date.fromisoformat(data.end_date),
        created_by_user_id=user_id,
    )
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return _to_dict(period)


async def activate_period(db: AsyncSession, period: SchedulePeriod) -> dict:
    if await check_active_exists(db, period.year, period.month):
        raise ValueError(f"Ya existe un periodo activo para {period.month}/{period.year}. Eliminalo primero.")

    period.status = "active"
    period.activated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(period)
    return _to_dict(period)


async def delete_period(db: AsyncSession, period: SchedulePeriod) -> None:
    await db.execute(delete(GenerationRun).where(GenerationRun.schedule_period_id == period.id))
    await db.execute(delete(ScheduleAssignment).where(ScheduleAssignment.schedule_period_id == period.id))
    await db.delete(period)
    await db.commit()


def _to_dict(p: SchedulePeriod) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "year": p.year,
        "month": p.month,
        "start_date": p.start_date.isoformat(),
        "end_date": p.end_date.isoformat(),
        "status": p.status,
        "activated_at": p.activated_at.isoformat() if p.activated_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
