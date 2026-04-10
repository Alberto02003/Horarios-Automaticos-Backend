from datetime import date, time

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schedule_assignment import ScheduleAssignment
from src.schemas.assignment import AssignmentCreate, AssignmentUpdate


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    parts = value.split(":")
    return time(int(parts[0]), int(parts[1]))


def _format_time(value: time | None) -> str | None:
    return value.strftime("%H:%M") if value else None


def _to_dict(a: ScheduleAssignment) -> dict:
    return {
        "id": a.id,
        "schedule_period_id": a.schedule_period_id,
        "member_id": a.member_id,
        "date": a.date.isoformat(),
        "shift_type_id": a.shift_type_id,
        "start_time": _format_time(a.start_time),
        "end_time": _format_time(a.end_time),
        "assignment_source": a.assignment_source,
        "is_locked": a.is_locked,
    }


async def list_assignments(db: AsyncSession, period_id: int) -> list[dict]:
    result = await db.execute(
        select(ScheduleAssignment)
        .where(ScheduleAssignment.schedule_period_id == period_id)
        .order_by(ScheduleAssignment.member_id, ScheduleAssignment.date)
    )
    return [_to_dict(a) for a in result.scalars().all()]


async def get_assignment(db: AsyncSession, assignment_id: int) -> ScheduleAssignment | None:
    result = await db.execute(select(ScheduleAssignment).where(ScheduleAssignment.id == assignment_id))
    return result.scalar_one_or_none()


async def create_assignment(db: AsyncSession, period_id: int, data: AssignmentCreate) -> dict:
    # Upsert: if assignment exists for same period+member+date, update it
    result = await db.execute(
        select(ScheduleAssignment).where(
            ScheduleAssignment.schedule_period_id == period_id,
            ScheduleAssignment.member_id == data.member_id,
            ScheduleAssignment.date == date.fromisoformat(data.date),
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.is_locked:
            return _to_dict(existing)  # Don't overwrite locked assignments
        existing.shift_type_id = data.shift_type_id
        existing.start_time = _parse_time(data.start_time)
        existing.end_time = _parse_time(data.end_time)
        existing.assignment_source = data.assignment_source
        await db.commit()
        await db.refresh(existing)
        return _to_dict(existing)

    assignment = ScheduleAssignment(
        schedule_period_id=period_id,
        member_id=data.member_id,
        date=date.fromisoformat(data.date),
        shift_type_id=data.shift_type_id,
        start_time=_parse_time(data.start_time),
        end_time=_parse_time(data.end_time),
        assignment_source=data.assignment_source,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return _to_dict(assignment)


async def bulk_create_assignments(db: AsyncSession, period_id: int, items: list[AssignmentCreate]) -> list[dict]:
    results = []
    for item in items:
        result = await create_assignment(db, period_id, item)
        results.append(result)
    return results


async def update_assignment(db: AsyncSession, assignment: ScheduleAssignment, data: AssignmentUpdate) -> dict:
    updates = data.model_dump(exclude_unset=True)
    if "start_time" in updates:
        updates["start_time"] = _parse_time(updates["start_time"])
    if "end_time" in updates:
        updates["end_time"] = _parse_time(updates["end_time"])
    for field, value in updates.items():
        setattr(assignment, field, value)
    await db.commit()
    await db.refresh(assignment)
    return _to_dict(assignment)


async def delete_assignment(db: AsyncSession, assignment: ScheduleAssignment) -> None:
    await db.delete(assignment)
    await db.commit()


async def bulk_update_assignments(db: AsyncSession, period_id: int, ids: list[int], shift_type_id: int | None, is_locked: bool | None) -> list[dict]:
    result = await db.execute(
        select(ScheduleAssignment).where(
            ScheduleAssignment.id.in_(ids),
            ScheduleAssignment.schedule_period_id == period_id,
        )
    )
    assignments = result.scalars().all()
    for a in assignments:
        if shift_type_id is not None:
            if not a.is_locked:
                a.shift_type_id = shift_type_id
        if is_locked is not None:
            a.is_locked = is_locked
    await db.commit()
    return [_to_dict(a) for a in assignments]


async def bulk_delete_assignments(db: AsyncSession, period_id: int, ids: list[int]) -> int:
    result = await db.execute(
        select(ScheduleAssignment).where(
            ScheduleAssignment.id.in_(ids),
            ScheduleAssignment.schedule_period_id == period_id,
            ScheduleAssignment.is_locked.is_(False),
        )
    )
    assignments = result.scalars().all()
    for a in assignments:
        await db.delete(a)
    await db.commit()
    return len(assignments)
