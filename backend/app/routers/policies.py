from fastapi import APIRouter
from backend.app.core.data_manager import get_dataframes
import math

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
        "clean_text": _safe(row.get("clean_text")),
        "updated_at": _safe(row.get("updated_at")),
    }


@router.get("")
def list_policies():
    policies_df, _ = get_dataframes()

    # 1차 NaN 제거
    policies_df = policies_df.where(policies_df.notna(), None)

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