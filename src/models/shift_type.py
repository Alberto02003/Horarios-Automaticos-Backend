from datetime import time

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Identity, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ShiftType(Base):
    __tablename__ = "shift_types"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    default_start_time: Mapped[time | None] = mapped_column(Time)
    default_end_time: Mapped[time | None] = mapped_column(Time)
    counts_as_work_time: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    color: Mapped[str] = mapped_column(Text, nullable=False, server_default="'#6B7280'")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    __table_args__ = (
        CheckConstraint(
            "category IN ('work', 'vacation', 'special')",
            name="ck_shift_types_category",
        ),
    )
