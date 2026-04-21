from abc import ABC, abstractmethod
from datetime import date, time, timedelta
from dataclasses import dataclass


@dataclass
class MemberInfo:
    id: int
    full_name: str
    weekly_hour_limit: float
    # Per-member rules from MemberGenerationPreference.preferences_jsonb.
    # None means "no constraint" — preserves behaviour for members without a row.
    allowed_shift_codes: frozenset[str] | None = None
    work_days: frozenset[int] | None = None  # weekday indices 0=Mon..6=Sun
    daily_hours: float | None = None
    # 7-tuple of shift codes (e.g. "M", "T", "D") — one per weekday Mon..Sun.
    # If set, the engine places exactly this code on each matching weekday and
    # skips all other logic (coverage/consecutive/rest) for that member.
    # Entries may be None to mean "engine decides" for that weekday.
    weekly_pattern: tuple[str | None, ...] | None = None

    def eligible_day(self, d: date) -> bool:
        return self.work_days is None or d.weekday() in self.work_days

    def eligible_shift(self, shift_code: str) -> bool:
        return self.allowed_shift_codes is None or shift_code in self.allowed_shift_codes

    def pattern_code_for(self, d: date) -> str | None:
        if self.weekly_pattern is None:
            return None
        return self.weekly_pattern[d.weekday()]

    def hours_for(self, shift: "ShiftInfo") -> float:
        # If the member has a custom daily cap (e.g. 5h reducción taking an 8h shift),
        # count only their contracted daily hours against the weekly limit.
        if self.daily_hours is not None and shift.counts_as_work_time:
            return min(shift.hours, self.daily_hours)
        return shift.hours


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
    shifts_by_code: dict[str, ShiftInfo]  # shift_code -> ShiftInfo (for pattern lookup)
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
