from abc import ABC, abstractmethod
from datetime import date, time, timedelta
from dataclasses import dataclass


@dataclass
class MemberInfo:
    id: int
    full_name: str
    weekly_hour_limit: float


@dataclass
class ShiftInfo:
    id: int
    code: str
    category: str
    start_time: time | None
    end_time: time | None
    counts_as_work_time: bool
    hours: float  # Computed duration


@dataclass
class ExistingAssignment:
    member_id: int
    date: date
    shift_type_id: int
    is_locked: bool


@dataclass
class ProposedAssignment:
    member_id: int
    date: date
    shift_type_id: int


@dataclass
class ShiftCoverage:
    min: int
    max: int


@dataclass
class GenerationContext:
    members: list[MemberInfo]
    work_shifts: list[ShiftInfo]
    all_shifts: dict[int, ShiftInfo]  # All shifts by id (for hour lookup)
    rest_shift_id: int | None
    existing: list[ExistingAssignment]
    dates: list[date]
    weekly_hour_limit: float
    max_consecutive_days: int
    min_rest_hours: int
    allow_weekend_work: bool
    fill_unassigned_only: bool
    shift_coverage: dict[int, ShiftCoverage]  # shift_type_id -> min/max per day


def compute_shift_hours(start: time | None, end: time | None) -> float:
    if not start or not end:
        return 8.0
    s = timedelta(hours=start.hour, minutes=start.minute)
    e = timedelta(hours=end.hour, minutes=end.minute)
    diff = e - s
    if diff.total_seconds() <= 0:
        diff += timedelta(hours=24)
    return diff.total_seconds() / 3600


class GenerationStrategy(ABC):
    @abstractmethod
    def generate(self, ctx: GenerationContext) -> list[ProposedAssignment]:
        ...
