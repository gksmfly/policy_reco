from fastapi import APIRouter
from ..schemas.recommend import RecommendRequest
from ..schemas.common import ok
from ..services.orchestration.recommend_flow import recommend_flow

router = APIRouter(prefix="/recommend", tags=["recommend"])

@router.post("")
def recommend(req: RecommendRequest):
    results = recommend_flow(req.dict())
    return ok(results)
