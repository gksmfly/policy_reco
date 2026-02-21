# -*- coding: utf-8 -*-
"""
build_clean_text.py

역할:
- policies.csv(또는 DB dump)의 여러 필드를 합쳐 RAG/검색/임베딩용 clean_text 생성
- __MISSING__ 같은 결측 표시값 제거
- 과도하게 긴 raw_text는 일부만 포함(섹션별 예산 방식으로 제한)
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


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
# main (budget version)
# -------------------------
def build_clean_text(
    row: Dict[str, Any],
    *,
    max_chars: int = 6000,
    include_raw_excerpt: bool = True,
) -> str:
    """
    섹션별 예산(budget) 방식으로 clean_text 생성.
    - 각 섹션마다 최대 글자 수를 배정해 중요한 섹션이 뒤에서 잘려 사라지지 않게 함.
    - 최종 결과는 max_chars를 넘지 않게 보장.

    포함 섹션:
    - [메타] 정책명/대상/요약
    - [지원대상] eligibility
    - [지원내용] benefit
    - [신청방법] apply_process
    - [신청기간] apply_period
    - [원문 일부] raw_text (옵션)

    max_chars: 최종 clean_text 최대 길이
    include_raw_excerpt: 원문 일부 포함 여부
    """

    def clip(v: Any, n: int) -> str:
        s = _clean_str(v)
        if not s or n <= 0:
            return ""
        return s[:n].rstrip()

    # 섹션별 글자 예산(필요하면 조정)
    budgets = {
        "meta": 500,
        "eligibility": 1400,
        "benefit": 1600,
        "apply_process": 800,
        "apply_period": 400,
        "raw": 1200,  # include_raw_excerpt=True일 때만 사용
    }

    parts: List[str] = []

    # 1) 메타
    policy_name = _first_non_empty(row, ["policy_name", "정책명", "servNm"])
    target_group = _first_non_empty(row, ["target_group", "대상"])
    summary = _first_non_empty(row, ["summary", "요약", "servDgst"])

    header_bits: List[str] = []
    if policy_name:
        header_bits.append(policy_name)
    if target_group:
        header_bits.append(f"대상: {target_group}")
    if summary:
        header_bits.append(f"요약: {summary}")

    meta = clip("\n".join(header_bits).strip(), budgets["meta"])
    if meta:
        parts.append("[메타]\n" + meta)

    # 2) 핵심 섹션들(각 섹션은 예산 안에서만 포함)
    eligibility = clip(row.get("eligibility"), budgets["eligibility"])
    if eligibility:
        parts.append("[지원대상]\n" + eligibility)

    benefit = clip(row.get("benefit"), budgets["benefit"])
    if benefit:
        parts.append("[지원내용]\n" + benefit)

    apply_process = clip(row.get("apply_process"), budgets["apply_process"])
    if apply_process:
        parts.append("[신청방법]\n" + apply_process)

    apply_period = clip(row.get("apply_period"), budgets["apply_period"])
    if apply_period:
        parts.append("[신청기간]\n" + apply_period)

    # 3) 원문 일부(마지막, 예산 제한)
    if include_raw_excerpt:
        raw = clip(row.get("raw_text"), budgets["raw"])
        if raw:
            parts.append("[원문 일부]\n" + raw)

    text = "\n\n".join(parts).strip()

    # 4) 최종 길이 제한(안전장치)
    if max_chars and len(text) > max_chars:
        text = text[:max_chars].rstrip()

    return text
