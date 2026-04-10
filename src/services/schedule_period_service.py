from datetime import date, datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schedule_period import SchedulePeriod
from src.schemas.schedule_period import PeriodCreate


async def list_periods(db: AsyncSession, offset: int = 0, limit: int = 50, include_inactive: bool = False) -> tuple[list[dict], int]:
    base = select(SchedulePeriod)
    if not include_inactive:
        base = base.where(SchedulePeriod.is_active.is_(True))
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0
    result = await db.execute(base.order_by(SchedulePeriod.year.desc(), SchedulePeriod.month.desc()).offset(offset).limit(limit))
    return [_to_dict(p) for p in result.scalars().all()], total


async def get_period(db: AsyncSession, period_id: int) -> SchedulePeriod | None:
    result = await db.execute(select(SchedulePeriod).where(SchedulePeriod.id == period_id))
    return result.scalar_one_or_none()


async def check_active_exists(db: AsyncSession, year: int, month: int) -> bool:
    result = await db.execute(
        select(SchedulePeriod).where(
            SchedulePeriod.year == year,
            SchedulePeriod.month == month,
            SchedulePeriod.status == "active",
            SchedulePeriod.is_active.is_(True),
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


async def delete_period(db: AsyncSession, period: SchedulePeriod) -> dict:
    period.is_active = False
    period.status = "draft"
    await db.commit()
    await db.refresh(period)
    return _to_dict(period)


def _to_dict(p: SchedulePeriod) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "year": p.year,
        "month": p.month,
        "start_date": p.start_date.isoformat(),
        "end_date": p.end_date.isoformat(),
        "status": p.status,
        "is_active": p.is_active,
        "activated_at": p.activated_at.isoformat() if p.activated_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
