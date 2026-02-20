from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.repositories.policy_repo import PolicyRepository
from ..schemas.common import ok

router = APIRouter(prefix="/policies", tags=["policies"])

@router.get("")
def list_policies(db: Session = Depends(get_db)):
    repo = PolicyRepository(db)
    data = repo.list_policies()
    return ok([p.__dict__ for p in data])

@router.get("/{policy_id}")
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    repo = PolicyRepository(db)
    policy = repo.get_policy(policy_id)
    return ok(policy.__dict__ if policy else None)
