from pydantic import BaseModel


class GenerationRequest(BaseModel):
    strategy: str = "balanced"  # balanced | coverage | conservative
    fill_unassigned_only: bool = True


class GenerationResponse(BaseModel):
    strategy: str
    proposals_count: int
    created_count: int


class GenerationRunResponse(BaseModel):
    id: int
    strategy: str
    input_snapshot_jsonb: dict | None = None
    result_summary_jsonb: dict | None = None
    created_at: str | None = None
