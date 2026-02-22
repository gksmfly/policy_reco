from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.core.data_manager import get_dataframes


def similar_flow(policy_id: str, top_k: int = 5) -> List[Dict]:
    """
    CSV 기반 유사 정책:
    - clean_text + policy_name 기반 TF-IDF 코사인 유사도
    - 외부 벡터DB/pgvector 없이 동작(데모용)
    """
    policies_df, _ = get_dataframes()
    df = policies_df.where(policies_df.notna(), None).copy()

    # policy_id 정규화
    try:
        target_id = int(policy_id)
    except Exception:
        return []

    if "policy_id" not in df.columns:
        return []

    df = df[df["policy_id"].notna()].copy()
    ids = df["policy_id"].astype(int).tolist()

    if target_id not in ids:
        return []

    # 텍스트 구성
    def _row_text(r):
        parts = [
            str(r.get("policy_name") or ""),
            str(r.get("support_summary") or ""),
            str(r.get("clean_text") or ""),
        ]
        return "\n".join([p for p in parts if p])

    texts = [_row_text(r) for r in df.to_dict(orient="records")]

    vec = TfidfVectorizer(max_features=20000)
    X = vec.fit_transform(texts)

    target_idx = ids.index(target_id)
    sims = cosine_similarity(X[target_idx], X).flatten()

    # 상위 top_k + 자기 자신 제외
    ranked_idx = np.argsort(-sims)
    out = []
    for idx in ranked_idx:
        pid = ids[idx]
        if pid == target_id:
            continue
        r = df.iloc[idx].to_dict()
        out.append(
            {
                "policy_id": str(pid),
                "policy_name": r.get("policy_name"),
                "similarity_score": float(sims[idx]),
                "summary": r.get("support_summary"),
                "detail": r.get("support_detail"),
                "region": r.get("region"),
            }
        )
        if len(out) >= top_k:
            break

    return out
