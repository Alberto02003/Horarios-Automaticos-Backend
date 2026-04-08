from abc import ABC, abstractmethod
from datetime import date, time
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
class GenerationContext:
    members: list[MemberInfo]
    work_shifts: list[ShiftInfo]  # Only shifts where counts_as_work_time=True
    rest_shift_id: int | None  # "Descanso" shift id
    existing: list[ExistingAssignment]
    dates: list[date]
    weekly_hour_limit: float
    max_consecutive_days: int
    min_rest_hours: int
    fill_unassigned_only: bool


class GenerationStrategy(ABC):
    @abstractmethod
    def generate(self, ctx: GenerationContext) -> list[ProposedAssignment]:
        ...
