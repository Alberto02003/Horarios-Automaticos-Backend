from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    member_id: int
    date: str  # YYYY-MM-DD
    shift_type_id: int
    start_time: str | None = None  # HH:MM
    end_time: str | None = None
    assignment_source: str = "manual"


class AssignmentUpdate(BaseModel):
    shift_type_id: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    is_locked: bool | None = None


class AssignmentBulkCreate(BaseModel):
    assignments: list[AssignmentCreate]


class AssignmentResponse(BaseModel):
    id: int
    schedule_period_id: int
    member_id: int
    date: str
    shift_type_id: int
    start_time: str | None = None
    end_time: str | None = None
    assignment_source: str
    is_locked: bool
