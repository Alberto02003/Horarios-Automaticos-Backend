from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    schedule_period_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    executed_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    strategy: Mapped[str] = mapped_column(Text, nullable=False)
    input_snapshot_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    result_summary_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_generation_runs_period_id", "schedule_period_id"),
        Index("ix_generation_runs_user_id", "executed_by_user_id"),
    )
