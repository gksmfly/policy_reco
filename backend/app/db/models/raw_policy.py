from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class RawPolicy(Base):
    __tablename__ = "raw_policies"

    policy_id: Mapped[str] = mapped_column(String, primary_key=True)

    source_url: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    version_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    source: Mapped[str | None] = mapped_column(String, nullable=True)
