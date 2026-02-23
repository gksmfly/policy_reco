from fastapi import APIRouter, Query
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.core.data_manager import get_dataframes

router = APIRouter(prefix="/similar", tags=["similar"])


def _json_safe(v):
    """
    JSON에 NaN/inf 못 들어가서 서버 터짐 방지.
    pandas/numpy scalar도 안전 변환.
    """
    if v is None:
        return None

    # numpy scalar -> python scalar
    if isinstance(v, (np.generic,)):
        v = v.item()

    # NaN / inf -> None
    try:
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return None
    except Exception:
        pass

    # pandas NA
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    return v


def _build_text(row):
    # NaN 섞여있으면 str(np.nan) = 'nan'이 돼서 품질 망가짐 → safe 처리
    parts = [
        _json_safe(row.get("policy_name", "")),
        _json_safe(row.get("support_summary", "")),
        _json_safe(row.get("support_detail", "")),
    ]
    return " ".join([str(p) for p in parts if isinstance(p, str) and p.strip()])


def _pick_base_policy(policy_input: str):
    """
    - 숫자면 policy_id로 찾기
    - 문자열이면 policy_name에서 공백 제거 후 contains 매칭
    """
    policies_df, _ = get_dataframes()
    policies_df = policies_df.copy()

    s = (policy_input or "").strip()
    if not s:
        return None

    # 1) 숫자면 ID lookup
    try:
        pid = int(float(s))
        hit = policies_df[policies_df["policy_id"] == pid]
        if not hit.empty:
            return hit.iloc[0]
    except Exception:
        pass

    # 2) 이름 매칭 (공백 제거)
    if "policy_name" not in policies_df.columns:
        return None

    normalized_input = s.replace(" ", "")
    policies_df["_normalized_name"] = (
        policies_df["policy_name"]
        .astype(str)
        .str.replace(" ", "", regex=False)
    )

    hit = policies_df[
        policies_df["_normalized_name"].str.contains(normalized_input, case=False, na=False)
    ]
    if not hit.empty:
        return hit.iloc[0]

    return None


@router.get("")
def similar_policies(
    policy_input: str = Query(...),
    top_k: int = Query(3, ge=1, le=20),
):
    policies_df, _ = get_dataframes()
    policies_df = policies_df.copy()

    base = _pick_base_policy(policy_input)
    if base is None:
        return {"base": None, "results": []}

    # base_id
    try:
        base_id = int(float(base.get("policy_id")))
    except Exception:
        base_id = None

    base_text = _build_text(base)
    if not base_text.strip():
        # base 텍스트가 비면 유사도 계산 불가
        return {"base": None, "results": []}

    # 전체 텍스트 구성
    # (여기서도 NaN 안전 처리된 텍스트만 사용)
    texts = policies_df.apply(_build_text, axis=1).tolist()

    # TF-IDF
    vectorizer = TfidfVectorizer(max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    base_vector = vectorizer.transform([base_text])

    similarities = cosine_similarity(base_vector, tfidf_matrix).flatten()

    # ✅ 유사도 NaN/inf 제거 (중요)
    similarities = np.nan_to_num(similarities, nan=0.0, posinf=0.0, neginf=0.0)

    policies_df["similarity"] = similarities

    # ✅ 동일 정책 제외
    if base_id is not None and "policy_id" in policies_df.columns:
        filtered_df = policies_df[policies_df["policy_id"].astype(str) != str(base_id)]
    else:
        filtered_df = policies_df

    # ✅ 유사도 높은 순
    filtered_df = filtered_df.sort_values(by="similarity", ascending=False).head(top_k)

    results = []
    for _, row in filtered_df.iterrows():
        sim = float(row.get("similarity", 0.0))
        sim_pct = round(sim * 100, 2)

        results.append({
            "policy_id": _json_safe(row.get("policy_id")),
            "policy_name": _json_safe(row.get("policy_name")),
            "summary": _json_safe(row.get("support_summary")),
            "detail": _json_safe(row.get("support_detail")),
            "region": _json_safe(row.get("region")),
            "similarity": _json_safe(sim_pct),
        })

    base_payload = {
        "policy_id": _json_safe(str(base_id) if base_id is not None else base.get("policy_id")),
        "policy_name": _json_safe(base.get("policy_name")),
        "summary": _json_safe(base.get("support_summary")),
        "detail": _json_safe(base.get("support_detail")),
        "region": _json_safe(base.get("region")),
    }

    # ✅ 응답 전체 2차 방어: 혹시라도 float nan 남아있으면 제거
    for r in results:
        for k in list(r.keys()):
            r[k] = _json_safe(r[k])

    for k in list(base_payload.keys()):
        base_payload[k] = _json_safe(base_payload[k])

    return {
        "base": base_payload,
        "results": results,
    }