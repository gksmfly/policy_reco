from pydantic import BaseModel
from typing import List

class RecommendRequest(BaseModel):
    age: int
    region: str
    household_size: int
    income_annual: int
    assets_total: int
    is_homeowner: bool
    vehicle_value: int

class RecommendItem(BaseModel):
    policy_id: str
    policy_name: str
    score: float
    rank: int
    matched_conditions: List[str]
    unmatched_conditions: List[str]
