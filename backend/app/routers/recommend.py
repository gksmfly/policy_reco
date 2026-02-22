from fastapi import APIRouter
from backend.app.schemas.recommend import RecommendRequest
from backend.app.services.orchestration.recommend_flow import recommend_flow

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("")
def recommend(req: RecommendRequest):
    results = recommend_flow(req.dict())
    return {"results": results}
