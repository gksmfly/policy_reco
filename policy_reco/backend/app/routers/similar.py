from fastapi import APIRouter
from backend.app.services.orchestration.similar_flow import similar_flow

router = APIRouter(prefix="/similar", tags=["similar"])

@router.get("/{policy_id}")
def similar(policy_id: str):
    results = similar_flow(policy_id)
    return {"results": results}
