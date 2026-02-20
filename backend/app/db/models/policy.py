from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class Policy(Base):
    __tablename__ = "policies"

    policy_id: Mapped[str] = mapped_column(String, primary_key=True)

    policy_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    support_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    region: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    clean_text: Mapped[str] = mapped_column(Text, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
