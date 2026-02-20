from __future__ import annotations

from datetime import datetime
import json

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    profile_json: Mapped[str] = mapped_column(Text, nullable=False)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)

    @staticmethod
    def dumps(obj) -> str:
        return json.dumps(obj, ensure_ascii=False)

    @staticmethod
    def loads(s: str):
        return json.loads(s)
