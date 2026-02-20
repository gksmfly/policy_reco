from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.policy import Policy

class PolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_policies(self, *, limit: int = 50, offset: int = 0) -> list[Policy]:
        stmt = select(Policy).order_by(Policy.updated_at.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        stmt = select(Policy).where(Policy.policy_id == policy_id)
        return self.db.execute(stmt).scalars().first()

    def search_policies(self, q: str, *, limit: int = 50, offset: int = 0) -> list[Policy]:
        pattern = f"%{q}%"
        stmt = (
            select(Policy)
            .where(
                (Policy.policy_name.like(pattern))
                | (Policy.support_summary.like(pattern))
                | (Policy.support_detail.like(pattern))
            )
            .order_by(Policy.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())
