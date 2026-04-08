from pydantic import BaseModel, Field


class MemberCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    role_name: str = Field(min_length=1, max_length=100)
    weekly_hour_limit: float = Field(gt=0)
    color_tag: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")
    metadata_jsonb: dict | None = None


class MemberUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    role_name: str | None = Field(default=None, min_length=1, max_length=100)
    weekly_hour_limit: float | None = Field(default=None, gt=0)
    is_active: bool | None = None
    color_tag: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    metadata_jsonb: dict | None = None


class MemberResponse(BaseModel):
    id: int
    full_name: str
    role_name: str
    weekly_hour_limit: float
    is_active: bool
    color_tag: str
    metadata_jsonb: dict | None = None
