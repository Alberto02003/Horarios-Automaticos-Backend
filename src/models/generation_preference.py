from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Identity, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class GenerationPreference(Base):
    __tablename__ = "generation_preferences"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    general_weekly_hour_limit: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    preferences_jsonb: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default='{"min_rest_hours": 12, "max_consecutive_days": 6, "allow_weekend_work": true, "prefer_balanced_distribution": true, "fill_unassigned_only": true}',
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("general_weekly_hour_limit > 0", name="ck_gen_prefs_positive_hours"),
    )
