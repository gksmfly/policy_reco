# backend/app/schemas/recommend.py

from pydantic import BaseModel
from typing import List


class RecommendRequest(BaseModel):
    age: int
    income: int
    assets: int
    is_homeless: bool


class RecommendItem(BaseModel):
    policy_id: str
    policy_name: str
    score: float
    rank: int
    matched_conditions: List[str]
    unmatched_conditions: List[str]