from __future__ import annotations

import math
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from backend.app.core.data_manager import get_dataframes

# .env 로드
load_dotenv()


# -----------------------------
# Utils
# -----------------------------
def _safe_json(v: Any) -> Any:
    """JSON 직렬화에서 nan/NaT 터지는거 방지."""
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except Exception:
        pass
    # pandas NaT
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    return v


def _normalize_similarity(score: Any) -> float:
    """
    llama_index node.score는 보통 0~1 코사인 유사도.
    혹시 이상값 나오면 0~1로 클램프.
    """
    try:
        s = float(score)
        if math.isnan(s) or math.isinf(s):
            return 0.0
    except Exception:
        return 0.0
    if s < 0:
        s = 0.0
    if s > 1:
        # 일부 설정에서 1 초과가 나오는 경우 대비
        s = 1.0
    return s


def _pick_text_for_index(row: pd.Series) -> str:
    """
    clean_text가 1순위.
    없으면 support_detail -> support_summary -> policy_name 순으로 fallback.
    """
    for key in ["clean_text", "support_detail", "support_summary", "policy_name"]:
        v = row.get(key)
        if isinstance(v, str):
            t = v.strip()
            if t:
                return t
    return ""


# -----------------------------
# Index + lookup cache
# -----------------------------
@lru_cache(maxsize=1)
def _build_index_and_lookup() -> Tuple[VectorStoreIndex, Dict[int, Dict[str, Any]]]:
    """
    - Vector index는 similar 검색용
    - lookup은 policy_id -> 정책 메타(요약/상세/지역/이름) 붙이기용
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    policies_df, _ = get_dataframes()
    # NaN -> None
    policies_df = policies_df.where(policies_df.notna(), None)

    documents: List[Document] = []
    lookup: Dict[int, Dict[str, Any]] = {}

    for _, row in policies_df.iterrows():
        pid = row.get("policy_id")
        try:
            pid_int = int(pid)
        except Exception:
            continue

        text = _pick_text_for_index(row)
        if not text:
            continue

        policy_name = row.get("policy_name")
        # ✅ metadata는 "짧게" (길면 Metadata length 에러남)
        documents.append(
            Document(
                text=text,
                metadata={
                    "policy_id": str(pid_int),
                    "policy_name": (policy_name or ""),
                },
            )
        )

        lookup[pid_int] = {
            "policy_id": pid_int,
            "policy_name": _safe_json(row.get("policy_name")),
            "summary": _safe_json(row.get("support_summary")),
            "detail": _safe_json(row.get("support_detail")),
            "region": _safe_json(row.get("region")),
            "clean_text": _safe_json(row.get("clean_text")),
            "updated_at": _safe_json(row.get("updated_at")),
        }

    if not documents:
        raise RuntimeError("Vector index용 문서가 비어 있습니다. (clean_text/support_detail 확인)")

    # OpenAI 설정
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.llm = OpenAI(model="gpt-4o")

    index = VectorStoreIndex.from_documents(documents)
    return index, lookup


# -----------------------------
# RAG 엔진 로드 (서버 시작 시 1회) - ✅ 유지해야 함
# -----------------------------
@lru_cache(maxsize=1)
def load_rag_engine():
    """
    Q&A용 chat engine.
    내부적으로 index를 재활용(중복 임베딩/문서 생성 방지)
    """
    index, _ = _build_index_and_lookup()

    chat_engine = index.as_chat_engine(
        llm=OpenAI(model="gpt-4o"),
        chat_mode="context",
        verbose=True,
    )
    return chat_engine


# -----------------------------
# 질문 처리
# -----------------------------
def ask_policy_question(question: str) -> str:
    if not question or not question.strip():
        return "질문을 입력해주세요."
    engine = load_rag_engine()
    response = engine.query(question)
    return str(response)


# -----------------------------
# Similar policies (vector)
# -----------------------------
def search_similar_policies(
    query_text: str,
    *,
    top_k: int = 3,
    exclude_policy_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    - similarity 80% 같은 필터 없음
    - top_k 만큼 최대한 채워서 반환
    - exclude_policy_id(자기 자신) 제외
    """
    query_text = (query_text or "").strip()
    if not query_text:
        return []

    index, lookup = _build_index_and_lookup()

    # 여유분 더 뽑아서 exclude/중복 제거 후 top_k 맞추기
    retriever = index.as_retriever(similarity_top_k=max(top_k * 5, top_k + 5))
    nodes = retriever.retrieve(query_text)

    results: List[Dict[str, Any]] = []
    seen: set[int] = set()

    for node in nodes:
        meta = getattr(node, "metadata", None) or {}
        pid_raw = meta.get("policy_id")

        try:
            pid = int(pid_raw)
        except Exception:
            continue

        if exclude_policy_id is not None and pid == exclude_policy_id:
            continue
        if pid in seen:
            continue

        seen.add(pid)

        base = lookup.get(pid, {})
        sim = _normalize_similarity(getattr(node, "score", 0.0))
        results.append(
            {
                "policy_id": str(pid),
                "policy_name": _safe_json(base.get("policy_name") or meta.get("policy_name")),
                "summary": _safe_json(base.get("summary")),
                "detail": _safe_json(base.get("detail")),
                "region": _safe_json(base.get("region")),
                # 프론트 표시용 (0~100)
                "similarity": round(sim * 100, 1),
            }
        )

        if len(results) >= top_k:
            break

    return results