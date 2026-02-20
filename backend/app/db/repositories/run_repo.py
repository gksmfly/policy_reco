from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.run_log import RecommendationRun

class RunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_run(
        self,
        *,
        profile: Dict[str, Any],
        results: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> RecommendationRun:
        run = RecommendationRun(
            user_id=user_id,
            created_at=created_at or datetime.utcnow(),
            profile_json=json.dumps(profile, ensure_ascii=False),
            results_json=json.dumps(results, ensure_ascii=False),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[RecommendationRun]:
        stmt = select(RecommendationRun).order_by(RecommendationRun.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def get_run(self, run_id: int) -> Optional[RecommendationRun]:
        stmt = select(RecommendationRun).where(RecommendationRun.id == run_id)
        return self.db.execute(stmt).scalars().first()
