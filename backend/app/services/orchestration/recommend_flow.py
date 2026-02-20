from typing import List, Dict, Any

def recommend_flow(profile: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
    # TODO: replace with real matcher integration
    return [
        {
            "policy_id": "P-0001",
            "policy_name": "샘플 정책",
            "score": 90.0,
            "rank": 1,
            "matched_conditions": ["연령 조건 충족"],
            "unmatched_conditions": []
        }
    ]
