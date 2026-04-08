"""Validation service: checks constraints and returns warnings (not hard blocks)."""

from datetime import time, timedelta, date
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schedule_assignment import ScheduleAssignment
from src.models.department_member import DepartmentMember
from src.models.shift_type import ShiftType
from src.models.generation_preference import GenerationPreference


def _hours_between(start: time | None, end: time | None) -> float:
    if not start or not end:
        return 8.0  # Default shift duration
    s = timedelta(hours=start.hour, minutes=start.minute)
    e = timedelta(hours=end.hour, minutes=end.minute)
    diff = e - s
    if diff.total_seconds() <= 0:
        diff += timedelta(hours=24)  # Night shift crossing midnight
    return diff.total_seconds() / 3600


async def validate_period(db: AsyncSession, period_id: int) -> list[dict]:
    """Returns a list of warning dicts: {type, member_id, message}"""
    warnings: list[dict] = []

    # Load data
    assignments_result = await db.execute(
        select(ScheduleAssignment).where(ScheduleAssignment.schedule_period_id == period_id)
    )
    assignments = list(assignments_result.scalars().all())

    members_result = await db.execute(select(DepartmentMember).where(DepartmentMember.is_active.is_(True)))
    members = {m.id: m for m in members_result.scalars().all()}

    shift_types_result = await db.execute(select(ShiftType))
    shift_types = {st.id: st for st in shift_types_result.scalars().all()}

    prefs_result = await db.execute(select(GenerationPreference))
    prefs = prefs_result.scalar_one_or_none()
    if not prefs:
        return warnings

    weekly_limit = float(prefs.general_weekly_hour_limit)
    pref_json = prefs.preferences_jsonb or {}
    max_consecutive = pref_json.get("max_consecutive_days", 6)

    # Group assignments by member
    by_member: dict[int, list[ScheduleAssignment]] = defaultdict(list)
    for a in assignments:
        by_member[a.member_id].append(a)

    for member_id, member_assignments in by_member.items():
        member = members.get(member_id)
        if not member:
            continue

        member_name = member.full_name
        member_limit = float(member.weekly_hour_limit)

        # Sort by date
        sorted_assignments = sorted(member_assignments, key=lambda a: a.date)

        # Total hours
        total_hours = 0.0
        work_dates: list[date] = []
        for a in sorted_assignments:
            st = shift_types.get(a.shift_type_id)
            if st and st.counts_as_work_time:
                hours = _hours_between(a.start_time or st.default_start_time, a.end_time or st.default_end_time)
                total_hours += hours
                work_dates.append(a.date)

        # Check weekly hour limit (approximate: total / weeks in period)
        if sorted_assignments:
            days_span = (sorted_assignments[-1].date - sorted_assignments[0].date).days + 1
            weeks = max(days_span / 7, 1)
            weekly_avg = total_hours / weeks
            limit = min(weekly_limit, member_limit)
            if weekly_avg > limit:
                warnings.append({
                    "type": "hours_exceeded",
                    "member_id": member_id,
                    "message": f"{member_name}: {weekly_avg:.1f}h/sem promedio (limite: {limit}h)",
                })

        # Check consecutive work days
        if work_dates:
            consecutive = 1
            for i in range(1, len(work_dates)):
                if (work_dates[i] - work_dates[i - 1]).days == 1:
                    consecutive += 1
                    if consecutive > max_consecutive:
                        warnings.append({
                            "type": "consecutive_days",
                            "member_id": member_id,
                            "message": f"{member_name}: {consecutive} dias consecutivos (max: {max_consecutive})",
                        })
                        break
                else:
                    consecutive = 1

    return warnings
