from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Identity, Index, Text, Time, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    schedule_period_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("schedule_periods.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("department_members.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    shift_type_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("shift_types.id"), nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    assignment_source: Mapped[str] = mapped_column(Text, nullable=False, server_default="'manual'")
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    details_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "assignment_source IN ('manual', 'auto', 'template')",
            name="ck_assignments_source",
        ),
        # Prevent duplicate assignments for same member on same date within a period
        UniqueConstraint("schedule_period_id", "member_id", "date", name="uq_assignments_period_member_date"),
        # FK indexes (PostgreSQL does NOT auto-index FKs)
        Index("ix_assignments_period_id", "schedule_period_id"),
        Index("ix_assignments_member_id", "member_id"),
        Index("ix_assignments_shift_type_id", "shift_type_id"),
        # Key query: assignments for a member in a date range
        Index("ix_assignments_member_date", "member_id", "date"),
    )
