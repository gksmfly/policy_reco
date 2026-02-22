from fastapi import APIRouter, Query
from backend.app.core.data_manager import get_dataframes
import math
from typing import Optional

router = APIRouter(prefix="/policies", tags=["policies"])


# -----------------------------
# NaN 안전 처리 함수
# -----------------------------
def _safe(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _serialize_policy(row: dict) -> dict:
    return {
        "policy_id": int(row.get("policy_id")) if row.get("policy_id") is not None else None,
        "policy_name": _safe(row.get("policy_name")),
        "summary": _safe(row.get("support_summary")),
        "detail": _safe(row.get("support_detail")),
        "region": _safe(row.get("region")),
        "updated_at": _safe(row.get("updated_at")),
    }


# ✅ 정책 검색 (policy_name 기준 ONLY)
@router.get("")
def list_policies(keyword: Optional[str] = Query(None)):
    policies_df, _ = get_dataframes()

    policies_df = policies_df.where(policies_df.notna(), None)

    # 🔥 핵심: policy_name 기준 필터
    if keyword:
        kw = keyword.strip().lower()
        policies_df = policies_df[
            policies_df["policy_name"]
            .astype(str)
            .str.lower()
            .str.contains(kw, na=False)
        ]

    records = policies_df.to_dict(orient="records")

    return {
        "results": [_serialize_policy(r) for r in records]
    }


@router.get("/{policy_id}")
def get_policy(policy_id: int):
    policies_df, _ = get_dataframes()

    row_df = policies_df[policies_df["policy_id"] == policy_id]

    if row_df.empty:
        return {"result": None}

    row_df = row_df.where(row_df.notna(), None)
    row = row_df.iloc[0].to_dict()

    return {
        "result": _serialize_policy(row)
    }