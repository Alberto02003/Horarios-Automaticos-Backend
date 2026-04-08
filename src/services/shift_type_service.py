from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.shift_type import ShiftType
from src.schemas.shift_type import ShiftTypeCreate, ShiftTypeUpdate


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    parts = value.split(":")
    return time(int(parts[0]), int(parts[1]))


def _format_time(value: time | None) -> str | None:
    if not value:
        return None
    return value.strftime("%H:%M")


async def list_shift_types(db: AsyncSession, include_inactive: bool = False) -> list[dict]:
    query = select(ShiftType).order_by(ShiftType.code)
    if not include_inactive:
        query = query.where(ShiftType.is_active.is_(True))
    result = await db.execute(query)
    return [_to_dict(st) for st in result.scalars().all()]


async def get_shift_type(db: AsyncSession, shift_type_id: int) -> ShiftType | None:
    result = await db.execute(select(ShiftType).where(ShiftType.id == shift_type_id))
    return result.scalar_one_or_none()


async def create_shift_type(db: AsyncSession, data: ShiftTypeCreate) -> dict:
    st = ShiftType(
        code=data.code,
        name=data.name,
        category=data.category,
        default_start_time=_parse_time(data.default_start_time),
        default_end_time=_parse_time(data.default_end_time),
        counts_as_work_time=data.counts_as_work_time,
        color=data.color,
    )
    db.add(st)
    await db.commit()
    await db.refresh(st)
    return _to_dict(st)


async def update_shift_type(db: AsyncSession, st: ShiftType, data: ShiftTypeUpdate) -> dict:
    updates = data.model_dump(exclude_unset=True)
    if "default_start_time" in updates:
        updates["default_start_time"] = _parse_time(updates["default_start_time"])
    if "default_end_time" in updates:
        updates["default_end_time"] = _parse_time(updates["default_end_time"])
    for field, value in updates.items():
        setattr(st, field, value)
    await db.commit()
    await db.refresh(st)
    return _to_dict(st)


def _to_dict(st: ShiftType) -> dict:
    return {
        "id": st.id,
        "code": st.code,
        "name": st.name,
        "category": st.category,
        "default_start_time": _format_time(st.default_start_time),
        "default_end_time": _format_time(st.default_end_time),
        "counts_as_work_time": st.counts_as_work_time,
        "color": st.color,
        "is_active": st.is_active,
    }
