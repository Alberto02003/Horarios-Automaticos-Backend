from sqlalchemy import BigInteger, Boolean, CheckConstraint, Identity, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class DepartmentMember(Base):
    __tablename__ = "department_members"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role_name: Mapped[str] = mapped_column(Text, nullable=False)
    weekly_hour_limit: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    color_tag: Mapped[str] = mapped_column(Text, nullable=False, server_default="'#3B82F6'")
    metadata_jsonb: Mapped[dict | None] = mapped_column(JSONB, server_default="{}")

    __table_args__ = (
        CheckConstraint("weekly_hour_limit > 0", name="ck_members_positive_hours"),
    )
