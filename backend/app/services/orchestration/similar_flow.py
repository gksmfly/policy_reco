from __future__ import annotations

from typing import Dict, List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.core.data_manager import get_dataframes


def _safe_value(v):
    """JSON 직렬화 안전 처리"""
    if v is None:
        return None
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        return 0.0
    return v


def similar_flow(policy_input: str, top_k: int = 5) -> List[Dict]:

    policies_df, _ = get_dataframes()
    df = policies_df.copy()

    if df.empty or "policy_id" not in df.columns:
        return []

    df = df[df["policy_id"].notna()].copy()
    df["policy_id"] = df["policy_id"].astype(int)

    # -----------------------------
    # 입력 처리
    # -----------------------------
    if policy_input.isdigit():
        target_id = int(policy_input)
        if target_id not in df["policy_id"].tolist():
            return []
    else:
        match = df[df["policy_name"] == policy_input]
        if match.empty:
            return []
        target_id = int(match.iloc[0]["policy_id"])

    # -----------------------------
    # 텍스트 구성
    # -----------------------------
    def _row_text(r):
        return "\n".join(
            [
                str(r.get("policy_name") or ""),
                str(r.get("support_summary") or ""),
                str(r.get("clean_text") or ""),
            ]
        )

    records = df.to_dict(orient="records")
    texts = [_row_text(r) for r in records]
    ids = [int(r["policy_id"]) for r in records]

    vec = TfidfVectorizer(max_features=20000)
    X = vec.fit_transform(texts)

    target_idx = ids.index(target_id)
    sims = cosine_similarity(X[target_idx], X).flatten()

    # 🔥 NaN / inf 제거
    sims = np.nan_to_num(sims, nan=0.0, posinf=0.0, neginf=0.0)

    ranked_idx = np.argsort(-sims)

    out = []

    for idx in ranked_idx:
        pid = ids[idx]
        if pid == target_id:
            continue

        r = records[idx]

        out.append(
            {
                "policy_id": str(pid),
                "policy_name": _safe_value(r.get("policy_name")),
                "similarity_score": float(_safe_value(sims[idx])),
                "summary": _safe_value(r.get("support_summary")),
                "detail": _safe_value(r.get("support_detail")),
                "region": _safe_value(r.get("region")),
            }
        )

        if len(out) >= top_k:
            break

    return out