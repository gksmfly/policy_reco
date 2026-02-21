# -*- coding: utf-8 -*-
"""
build_clean_text.py

역할:
- policies.csv(또는 DB dump)의 여러 필드를 합쳐 RAG/검색/임베딩용 clean_text 생성
- __MISSING__ 같은 결측 표시값 제거
- 과도하게 긴 raw_text는 일부만 포함(기본 2000자)
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


MISSING_VALUE = "__MISSING__"


# -------------------------
# helpers
# -------------------------
def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    return (s == "") or (s.lower() == "nan") or (s == MISSING_VALUE)


def _clean_str(v: Any) -> str:
    if _is_missing(v):
        return ""
    s = str(v).replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _add_section(parts: List[str], title: str, body: str) -> None:
    body = _clean_str(body)
    if body:
        parts.append(f"[{title}]\n{body}")


def _first_non_empty(row: Dict[str, Any], keys: Iterable[str]) -> str:
    for k in keys:
        v = _clean_str(row.get(k))
        if v:
            return v
    return ""


# -------------------------
# main
# -------------------------
def build_clean_text(
    row: Dict[str, Any],
    *,
    max_chars: int = 6000,
    raw_excerpt_chars: int = 2000,
    include_raw_excerpt: bool = True,
) -> str:
    """
    row에서 clean_text 생성.

    기본 포함 섹션:
    - 정책명, 대상, 요약
    - 지원대상(eligibility)
    - 지원내용(benefit)
    - 신청방법(apply_process)
    - 신청기간(apply_period)
    - (선택) 원문 일부(raw_text)

    max_chars: 최종 clean_text 최대 길이(초과 시 잘라냄)
    raw_excerpt_chars: raw_text를 포함할 때 최대 몇 자까지 붙일지
    """
    parts: List[str] = []

    # 1) 정책명/대상/요약: 한 번에 상단 컨텍스트로 제공
    policy_name = _first_non_empty(row, ["policy_name", "정책명", "servNm"])
    target_group = _first_non_empty(row, ["target_group", "대상"])
    summary = _first_non_empty(row, ["summary", "요약", "servDgst"])

    header_bits = []
    if policy_name:
        header_bits.append(policy_name)
    if target_group:
        header_bits.append(f"대상: {target_group}")
    if summary:
        header_bits.append(f"요약: {summary}")

    if header_bits:
        parts.append("[메타]\n" + "\n".join(header_bits))

    # 2) 핵심 섹션들
    _add_section(parts, "지원대상", row.get("eligibility"))
    _add_section(parts, "지원내용", row.get("benefit"))
    _add_section(parts, "신청방법", row.get("apply_process"))
    _add_section(parts, "신청기간", row.get("apply_period"))

    # 3) 원문 일부(선택)
    if include_raw_excerpt:
        raw_text = _clean_str(row.get("raw_text"))
        if raw_text:
            excerpt = raw_text[: max(0, int(raw_excerpt_chars))]
            _add_section(parts, "원문 일부", excerpt)

    text = "\n\n".join(parts).strip()

    # 4) 최종 길이 제한
    if max_chars and len(text) > max_chars:
        text = text[:max_chars].rstrip()

    return text