from pydantic import BaseModel, Field


class ShiftTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=10)
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(pattern=r"^(work|vacation|special)$")
    default_start_time: str | None = None  # "HH:MM"
    default_end_time: str | None = None
    counts_as_work_time: bool = True
    color: str = Field(default="#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")


class ShiftTypeUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=10)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, pattern=r"^(work|vacation|special)$")
    default_start_time: str | None = None
    default_end_time: str | None = None
    counts_as_work_time: bool | None = None
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_active: bool | None = None


class ShiftTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    default_start_time: str | None = None
    default_end_time: str | None = None
    counts_as_work_time: bool
    color: str
    is_active: bool
