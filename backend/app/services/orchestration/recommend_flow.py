from __future__ import annotations

from typing import Any, Dict, List
import os
import pandas as pd
import numpy as np

from backend.app.core.data_manager import get_dataframes, get_csv_paths
from backend.app.pipeline.rag_filter_ver3 import filter_policies_from_csv


def _safe(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def _resolve_eligibility_path() -> str:
    env_path = os.getenv("POLICY_ELIGIBILITY_CSV_PATH")

    if env_path:
        path = env_path
    else:
        path = get_csv_paths()[1]

    if not os.path.isabs(path):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        path = os.path.join(base_dir, path)

    return path


def _normalize_pid(pid) -> str | None:
    """
    policy_id가 '101', 101, 101.0, '101 ' 등으로 섞여와도
    동일 정책으로 인식하도록 정규화
    """
    if pid is None:
        return None
    try:
        s = str(pid).strip()
        if s == "":
            return None
        # '101.0' 같은 경우도 int로 정규화
        return str(int(float(s)))
    except Exception:
        return None


def recommend_flow(profile: Dict[str, Any], top_k: int = 5) -> Dict[str, Any]:
    policies_df, _ = get_dataframes()

    age = int(profile.get("age") or 0)
    annual_income = profile.get("income")
    assets = profile.get("assets")
    is_homeless = profile.get("is_homeless")

    eligibility_path = _resolve_eligibility_path()

    result = filter_policies_from_csv(
        eligibility_path,
        age=age,
        annual_income=int(annual_income) if annual_income not in (None, "") else None,
        assets=int(assets) if assets not in (None, "") else None,
        is_homeless=bool(is_homeless) if is_homeless is not None else None,
        vehicle_value=None,
    )

    passed = result.get("passed", []) or []

    # ✅ 1) passed 단계에서 policy_id 정규화 + 중복 제거
    unique_passed_by_pid: Dict[str, Dict[str, Any]] = {}
    for p in passed:
        pid_norm = _normalize_pid(p.get("policy_id"))
        if pid_norm is None:
            continue
        if pid_norm not in unique_passed_by_pid:
            unique_passed_by_pid[pid_norm] = p

    passed = list(unique_passed_by_pid.values())

    # 정책 메타데이터 lookup (policy_id 정규화해서 키 맞추기)
    clean_df = policies_df.copy()
    clean_df = clean_df.replace({pd.NA: None})
    clean_df = clean_df.where(pd.notnull(clean_df), None)

    lookup: Dict[str, Dict[str, Any]] = {}
    for r in clean_df.to_dict(orient="records"):
        pid_norm = _normalize_pid(r.get("policy_id"))
        if pid_norm is None:
            continue
        if pid_norm not in lookup:
            lookup[pid_norm] = r

    items: List[Dict[str, Any]] = []

    for p in passed:
        pid_norm = _normalize_pid(p.get("policy_id"))
        if pid_norm is None:
            continue

        meta = lookup.get(pid_norm, {})
        explain = p.get("explain", {}) or {}

        matched = explain.get("passed", []) or []
        skipped = explain.get("skipped", []) or []
        failed = explain.get("failed", []) or []

        score = float(80 + 5 * len(matched) - 2 * len(skipped))
        if pd.isna(score) or np.isinf(score):
            score = 0.0

        items.append(
            {
                "policy_id": pid_norm,
                "policy_name": _safe(meta.get("policy_name")),
                "score": score,
                "matched_conditions": matched,
                "unmatched_conditions": failed,
                "summary": _safe(meta.get("support_summary")),
                "detail": _safe(meta.get("support_detail")),
                "region": _safe(meta.get("region")),
            }
        )

    # ✅ 2) 화면상 “동일 정책명 반복” 방지: policy_name 기준 2차 중복 제거
    # (정책명이 아예 같으면 하나만 남김. 점수가 높은 것 우선)
    items.sort(key=lambda x: x.get("score", 0), reverse=True)

    deduped: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    for it in items:
        name = (it.get("policy_name") or "").strip()
        # 이름이 비어있으면 id 기준으로만
        if name:
            if name in seen_names:
                continue
            seen_names.add(name)
        deduped.append(it)

    items = deduped[:top_k]

    for i, it in enumerate(items, start=1):
        it["rank"] = i

    # JSON 안전 처리
    for it in items:
        for k, v in it.items():
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                it[k] = None

    return {"results": items}