# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def norm_text(text: str) -> str:
    if text is None:
        return ""
    t = str(text)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    # 공백 정리
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def find_all(pattern: str, text: str, flags: int = re.IGNORECASE) -> List[re.Match]:
    return list(re.finditer(pattern, text, flags))


def to_int_safe(s: str) -> Optional[int]:
    s = re.sub(r"[^\d]", "", s)
    if not s:
        return None
    try:
        return int(s)
    except Exception:
        return None


def parse_money_to_won(s: str) -> Optional[int]:
    """
    한국어 금액 표현을 '원' 단위 int로 근사 변환.
    지원: 만/억 + 숫자(정수). (소수는 버림)
    예)
      "200만원" -> 2_000_000
      "1억" -> 100_000_000
      "1억 2천만원" 같은 복합은 1차 버전에선 부분 매칭만 될 수 있음.
    """
    if not s:
        return None
    s = s.replace(",", "").replace(" ", "")

    # 1) 억 단위
    m = re.search(r"(\d+)\s*억", s)
    total = 0
    if m:
        v = to_int_safe(m.group(1))
        if v is not None:
            total += v * 100_000_000

    # 2) 만 단위
    m2 = re.search(r"(\d+)\s*만", s)
    if m2:
        v2 = to_int_safe(m2.group(1))
        if v2 is not None:
            total += v2 * 10_000

    # 3) 원/천원/만원/백만원/천만원 등 숫자원 (간단 처리)
    m3 = re.search(r"(\d+)\s*원", s)
    if m3:
        v3 = to_int_safe(m3.group(1))
        if v3 is not None:
            total += v3

    return total if total > 0 else None


def result_template(entity: str) -> Dict[str, Any]:
    return {
        "entity": entity,
        "constraints": [],     # 조건 리스트
        "notes": [],           # 애매한 문구/추가정보
        "evidence": [],        # (필요 시) 매칭된 원문 조각
    }