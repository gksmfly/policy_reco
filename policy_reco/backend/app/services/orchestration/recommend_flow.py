from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd

from backend.app.core.data_manager import get_dataframes, get_csv_paths
from backend.app.pipeline.rag_filter_ver3 import filter_policies_from_csv


def _safe(value):
    """
    pandas NaN / numpy.nan → None 변환
    JSON 직렬화 안전 처리
    """
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def recommend_flow(profile: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    CSV 기반 추천:
    - policy_eligibility.csv 로 하드 필터
    - policies.csv 에서 정책 메타정보 붙임
    - 점수는 통과 조건 개수 기반 휴리스틱
    """

    policies_df, _ = get_dataframes()

    # ===== 프론트 기준 필드 =====
    age = int(profile.get("age") or 0)
    annual_income = profile.get("income")
    assets = profile.get("assets")
    is_homeless = profile.get("is_homeless")

    # ===== 하드 필터 실행 =====
    result = filter_policies_from_csv(
        get_csv_paths()[1],
        age=age,
        annual_income=int(annual_income) if annual_income not in (None, "") else None,
        assets=int(assets) if assets not in (None, "") else None,
        is_homeless=bool(is_homeless) if is_homeless is not None else None,
        vehicle_value=None,
    )

    passed = result.get("passed", [])

    # ===== NaN 제거한 metadata lookup 생성 =====
    clean_df = policies_df.copy()
    clean_df = clean_df.replace({pd.NA: None})
    clean_df = clean_df.where(pd.notnull(clean_df), None)

    lookup = {
        int(r["policy_id"]): r
        for r in clean_df.to_dict(orient="records")
        if r.get("policy_id") is not None
    }

    items: List[Dict[str, Any]] = []

    # ===== 추천 결과 구성 =====
    for p in passed:
        pid = p.get("policy_id")

        try:
            pid_int = int(pid)
        except Exception:
            continue

        meta = lookup.get(pid_int, {})
        explain = p.get("explain", {})

        matched = explain.get("passed", []) or []
        skipped = explain.get("skipped", []) or []
        failed = explain.get("failed", []) or []

        # 점수 계산
        score = float(80 + 5 * len(matched) - 2 * len(skipped))

        # 혹시라도 NaN 방어
        if pd.isna(score):
            score = 0.0

        items.append(
            {
                "policy_id": str(pid_int),
                "policy_name": _safe(meta.get("policy_name")),
                "score": score,
                "matched_conditions": matched,
                "unmatched_conditions": failed,
                "summary": _safe(meta.get("support_summary")),
                "detail": _safe(meta.get("support_detail")),
                "region": _safe(meta.get("region")),
            }
        )

    # ===== 정렬 + top_k =====
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    items = items[:top_k]

    # ===== rank 부여 =====
    for i, it in enumerate(items, start=1):
        it["rank"] = i

    return items