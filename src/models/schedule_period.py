from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, Identity, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SchedulePeriod(Base):
    __tablename__ = "schedule_periods"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="'draft'")
    generation_summary_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'active')", name="ck_periods_status"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_periods_month"),
        CheckConstraint("start_date <= end_date", name="ck_periods_date_range"),
        Index("ix_schedule_periods_year_month", "year", "month"),
        Index("ix_schedule_periods_created_by", "created_by_user_id"),
    )
