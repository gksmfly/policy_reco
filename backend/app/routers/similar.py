from fastapi import APIRouter, Query
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from backend.app.core.data_manager import get_dataframes

router = APIRouter(prefix="/similar", tags=["similar"])


def _pick_base_policy(policy_input: str):
    policies_df, _ = get_dataframes()
    policies_df = policies_df.where(policies_df.notna(), None)

    s = (policy_input or "").strip()
    if not s:
        return None

    # 숫자 → policy_id
    try:
        pid = int(s)
        hit = policies_df[policies_df["policy_id"] == pid]
        if not hit.empty:
            return hit.iloc[0]
    except Exception:
        pass

    # 문자열 → policy_name contains
    if "policy_name" in policies_df.columns:
        hit = policies_df[
            policies_df["policy_name"]
            .astype(str)
            .str.contains(s, case=False, na=False)
        ]
        if not hit.empty:
            return hit.iloc[0]

    return None


def _build_text(row):
    return " ".join([
        str(row.get("policy_name", "")),
        str(row.get("support_summary", "")),
        str(row.get("support_detail", "")),
    ])


@router.get("")
def similar_policies(
    policy_input: str = Query(...),
    top_k: int = Query(3, ge=1, le=20),
):
    policies_df, _ = get_dataframes()
    policies_df = policies_df.fillna("")

    base = _pick_base_policy(policy_input)
    if base is None:
        return {"base": None, "results": []}

    base_id = str(base.get("policy_id"))
    base_text = _build_text(base)

    # 🔥 TF-IDF 벡터화
    texts = policies_df.apply(_build_text, axis=1).tolist()

    vectorizer = TfidfVectorizer(max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)

    base_vector = vectorizer.transform([base_text])

    similarities = cosine_similarity(base_vector, tfidf_matrix).flatten()
    similarities = np.nan_to_num(similarities)

    policies_df["similarity"] = similarities

    # 🔥 동일 정책 제거
    filtered_df = policies_df[
        policies_df["policy_id"].astype(str) != base_id
    ]

    # 🔥 유사도 높은 순 정렬
    filtered_df = filtered_df.sort_values(
        by="similarity", ascending=False
    ).head(top_k)

    results = []

    for _, row in filtered_df.iterrows():
        similarity_percent = round(float(row["similarity"]) * 100, 2)

        results.append({
            "policy_id": str(row.get("policy_id")),
            "policy_name": row.get("policy_name"),
            "summary": row.get("support_summary"),
            "detail": row.get("support_detail"),
            "region": row.get("region"),
            "similarity": similarity_percent,
        })

    return {
        "base": {
            "policy_id": base_id,
            "policy_name": base.get("policy_name"),
            "summary": base.get("support_summary"),
            "detail": base.get("support_detail"),
            "region": base.get("region"),
        },
        "results": results,
    }