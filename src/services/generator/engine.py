"""Generation engine: loads data, runs strategy, saves results."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.department_member import DepartmentMember
from src.models.shift_type import ShiftType
from src.models.schedule_period import SchedulePeriod
from src.models.schedule_assignment import ScheduleAssignment
from src.models.generation_preference import GenerationPreference
from src.models.generation_run import GenerationRun
from src.schemas.assignment import AssignmentCreate
from src.services import assignment_service

from .base import GenerationContext, MemberInfo, ShiftInfo, ShiftCoverage, ExistingAssignment, compute_shift_hours
from .balanced import BalancedStrategy
from .coverage import CoverageStrategy
from .conservative import ConservativeStrategy

STRATEGIES = {
    "balanced": BalancedStrategy,
    "coverage": CoverageStrategy,
    "conservative": ConservativeStrategy,
}


async def run_generation(
    db: AsyncSession,
    period_id: int,
    user_id: int,
    strategy_name: str,
    fill_unassigned_only: bool = True,
) -> dict:
    # Load period
    period_result = await db.execute(select(SchedulePeriod).where(SchedulePeriod.id == period_id))
    period = period_result.scalar_one()

    # Load members
    members_result = await db.execute(
        select(DepartmentMember).where(DepartmentMember.is_active.is_(True)).order_by(DepartmentMember.full_name)
    )
    members = [
        MemberInfo(id=m.id, full_name=m.full_name, weekly_hour_limit=float(m.weekly_hour_limit))
        for m in members_result.scalars().all()
    ]

    # Load shift types
    shifts_result = await db.execute(select(ShiftType).where(ShiftType.is_active.is_(True)))
    all_shifts = list(shifts_result.scalars().all())
    all_shifts_map: dict[int, ShiftInfo] = {}
    work_shifts: list[ShiftInfo] = []
    for s in all_shifts:
        si = ShiftInfo(
            id=s.id, code=s.code, category=s.category,
            start_time=s.default_start_time, end_time=s.default_end_time,
            counts_as_work_time=s.counts_as_work_time,
            hours=compute_shift_hours(s.default_start_time, s.default_end_time),
        )
        all_shifts_map[s.id] = si
        if s.counts_as_work_time:
            work_shifts.append(si)
    rest_shift = next((s for s in all_shifts if s.code == "D"), None)

    # Load existing assignments
    existing_result = await db.execute(
        select(ScheduleAssignment).where(ScheduleAssignment.schedule_period_id == period_id)
    )
    existing = [
        ExistingAssignment(member_id=a.member_id, date=a.date, shift_type_id=a.shift_type_id, is_locked=a.is_locked)
        for a in existing_result.scalars().all()
    ]

    # Load preferences
    prefs_result = await db.execute(select(GenerationPreference))
    prefs = prefs_result.scalar_one_or_none()
    pref_json = (prefs.preferences_jsonb if prefs else {}) or {}

    # Build date range
    dates: list[date] = []
    current = period.start_date
    while current <= period.end_date:
        dates.append(current)
        from datetime import timedelta
        current += timedelta(days=1)

    # Build context
    ctx = GenerationContext(
        members=members,
        work_shifts=work_shifts,
        all_shifts=all_shifts_map,
        rest_shift_id=rest_shift.id if rest_shift else None,
        existing=existing,
        dates=dates,
        weekly_hour_limit=float(prefs.general_weekly_hour_limit) if prefs else 40.0,
        max_consecutive_days=pref_json.get("max_consecutive_days", 6),
        min_rest_hours=pref_json.get("min_rest_hours", 12),
        allow_weekend_work=pref_json.get("allow_weekend_work", True),
        fill_unassigned_only=fill_unassigned_only,
        shift_coverage={
            int(k): ShiftCoverage(min=v.get("min", 0), max=v.get("max", 99))
            for k, v in (pref_json.get("shift_coverage") or {}).items()
        },
    )

    # Run strategy
    strategy_cls = STRATEGIES.get(strategy_name)
    if not strategy_cls:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    strategy = strategy_cls()
    proposals = strategy.generate(ctx)

    # Save assignments
    created_count = 0
    for p in proposals:
        await assignment_service.create_assignment(db, period_id, AssignmentCreate(
            member_id=p.member_id,
            date=p.date.isoformat(),
            shift_type_id=p.shift_type_id,
            assignment_source="auto",
        ))
        created_count += 1

    # Save generation run
    run = GenerationRun(
        schedule_period_id=period_id,
        executed_by_user_id=user_id,
        strategy=strategy_name,
        input_snapshot_jsonb={
            "members_count": len(members),
            "dates_count": len(dates),
            "existing_count": len(existing),
            "fill_unassigned_only": fill_unassigned_only,
        },
        result_summary_jsonb={
            "proposals_count": len(proposals),
            "created_count": created_count,
        },
    )
    db.add(run)
    await db.commit()

    return {
        "strategy": strategy_name,
        "proposals_count": len(proposals),
        "created_count": created_count,
    }


async def list_generation_runs(db: AsyncSession, period_id: int) -> list[dict]:
    result = await db.execute(
        select(GenerationRun)
        .where(GenerationRun.schedule_period_id == period_id)
        .order_by(GenerationRun.created_at.desc())
    )
    return [
        {
            "id": r.id,
            "strategy": r.strategy,
            "input_snapshot_jsonb": r.input_snapshot_jsonb,
            "result_summary_jsonb": r.result_summary_jsonb,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in result.scalars().all()
    ]
