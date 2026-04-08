from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schedule_period import SchedulePeriod
from src.schemas.schedule_period import PeriodCreate


async def list_periods(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(SchedulePeriod).order_by(SchedulePeriod.year.desc(), SchedulePeriod.month.desc()))
    return [_to_dict(p) for p in result.scalars().all()]


async def get_period(db: AsyncSession, period_id: int) -> SchedulePeriod | None:
    result = await db.execute(select(SchedulePeriod).where(SchedulePeriod.id == period_id))
    return result.scalar_one_or_none()


async def create_period(db: AsyncSession, data: PeriodCreate, user_id: int) -> dict:
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
    period.status = "active"
    period.activated_at = datetime.now(timezone.utc)
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
        "activated_at": p.activated_at.isoformat() if p.activated_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
