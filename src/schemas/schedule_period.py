from pydantic import BaseModel, Field


class PeriodCreate(BaseModel):
    name: str = Field(min_length=1)
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)
    start_date: str  # YYYY-MM-DD
    end_date: str


class PeriodResponse(BaseModel):
    id: int
    name: str
    year: int
    month: int
    start_date: str
    end_date: str
    status: str
    activated_at: str | None = None
    created_at: str
