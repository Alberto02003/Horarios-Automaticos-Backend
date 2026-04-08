from pydantic import BaseModel, Field


class GlobalPreferencesResponse(BaseModel):
    id: int
    general_weekly_hour_limit: float
    preferences_jsonb: dict


class GlobalPreferencesUpdate(BaseModel):
    general_weekly_hour_limit: float | None = Field(default=None, gt=0)
    preferences_jsonb: dict | None = None


class MemberPreferencesResponse(BaseModel):
    id: int
    member_id: int
    preferences_jsonb: dict


class MemberPreferencesUpdate(BaseModel):
    preferences_jsonb: dict
