from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class MemberGenerationPreference(Base):
    __tablename__ = "member_generation_preferences"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    member_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    preferences_jsonb: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_member_gen_prefs_member_id", "member_id"),
    )
