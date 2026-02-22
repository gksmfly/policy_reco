from fastapi import APIRouter
from typing import Dict

from backend.app.services.orchestration.recommend_flow import recommend_flow

router = APIRouter(prefix="/recommend", tags=["Recommend"])


@router.post("/")
def recommend(profile: Dict):
    return recommend_flow(profile)