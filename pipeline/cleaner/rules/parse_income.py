# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .utils import norm_text, to_int_safe, parse_money_to_won, result_template


def parse_income(text: str) -> Dict[str, Any]:
    t = norm_text(text)
    out = result_template("income")
    if not t:
        return out

    # 내부 유틸
    def _op_to_maxmin(op: str) -> Optional[str]:
        op = (op or "").strip()
        if op in ("이하", "미만", "이내"):
            return "max"
        if op in ("이상", "초과"):
            return "min"
        return None

    def _append_constraint(ctype: str, value: int, op: Optional[str], ev: str) -> None:
        # 중복 방지(같은 type/value/op가 이미 있으면 스킵)
        key = (ctype, int(value), op or "")
        for c in out["constraints"]:
            if isinstance(c, dict) and (c.get("type"), c.get("value"), c.get("op", "")) == key:
                return
        payload = {"type": ctype, "value": int(value)}
        if op:
            payload["op"] = op
        out["constraints"].append(payload)
        out["evidence"].append(ev)

    # ---------------------------------------------------------------------
    # 1) 중위소득 % (가장 우선/명확)
    # ---------------------------------------------------------------------
    # 예: 기준 중위소득 150% 이하, 중위 소득 120% 이내, 중위소득 100% 이상
    for m in re.finditer(
        r"(?:기준\s*)?중위\s*소득\s*(\d{1,3})\s*%\s*(이하|미만|이내|이상|초과)",
        t,
        re.IGNORECASE,
    ):
        p = to_int_safe(m.group(1))
        if p is None:
            continue
        op_word = m.group(2)
        mm = _op_to_maxmin(op_word)
        if mm == "max":
            _append_constraint("median_percent_max", p, "max", m.group(0))
        elif mm == "min":
            _append_constraint("median_percent_min", p, "min", m.group(0))

    # ---------------------------------------------------------------------
    # 2) 비-중위소득 % (평균/기준/도시근로자월평균/그냥 소득)
    # ---------------------------------------------------------------------
    # 예: 도시근로자 월평균소득 120% 이하, 평균소득 80% 이하, 소득 70% 이내
    # "중위소득"은 위에서 이미 처리하므로 제외(negative lookahead)
    for m in re.finditer(
        r"(?!.*중위\s*소득)"
        r"(?:도시근로자\s*월평균\s*)?(?:평균\s*)?(?:기준\s*)?소득\s*(\d{1,3})\s*%\s*(이하|미만|이내|이상|초과)",
        t,
        re.IGNORECASE,
    ):
        p = to_int_safe(m.group(1))
        if p is None:
            continue
        op_word = m.group(2)
        mm = _op_to_maxmin(op_word)
        if mm == "max":
            _append_constraint("percent_max", p, "max", m.group(0))
        elif mm == "min":
            _append_constraint("percent_min", p, "min", m.group(0))

    # ---------------------------------------------------------------------
    # 3) 금액 조건: 연소득/월소득
    # ---------------------------------------------------------------------
    # 예: 연소득 6,000만원 이하 / 월소득 300만원 미만 / 연 소득 50000000원 이하
    for m in re.finditer(
        r"(연\s*소득|월\s*소득)\s*([0-9][0-9,]*)\s*(만원|원)\s*(이하|미만|이내|이상|초과)",
        t,
        re.IGNORECASE,
    ):
        kind = (m.group(1) or "").replace(" ", "")  # '연소득' / '월소득'
        amount_num = m.group(2)
        unit = m.group(3)
        op_word = m.group(4)

        won = parse_money_to_won(f"{amount_num}{unit}")
        if won is None:
            continue

        mm = _op_to_maxmin(op_word)
        if "연" in kind:
            if mm == "max":
                _append_constraint("annual_max_won", won, "max", m.group(0))
            elif mm == "min":
                _append_constraint("annual_min_won", won, "min", m.group(0))
        else:
            if mm == "max":
                _append_constraint("monthly_max_won", won, "max", m.group(0))
            elif mm == "min":
                _append_constraint("monthly_min_won", won, "min", m.group(0))

    # ---------------------------------------------------------------------
    # 4) 분위(소득분위/분위) - 단순
    # ---------------------------------------------------------------------
    for m in re.finditer(r"(\d{1,2})\s*분위", t, re.IGNORECASE):
        v = to_int_safe(m.group(1))
        if v is None:
            continue
        # 보통 1~10이 합리적. 범위를 벗어나면 note로만 남김.
        if 1 <= v <= 10:
            _append_constraint("decile", v, None, m.group(0))
        else:
            out["notes"].append(f"분위 값 범위가 비정상일 수 있음: {m.group(0)}")
            out["evidence"].append(m.group(0))

    # ---------------------------------------------------------------------
    # 5) 애매/복잡한 패턴은 notes로만 남김(가구원수별 등)
    # ---------------------------------------------------------------------
    # 예: "1인 120%, 2인 110%..." 같은 경우: 숫자/%가 여러 개 붙는 패턴
    if re.search(r"\d+인\s*\d{1,3}\s*%", t):
        out["notes"].append("가구원수별 소득% 조건이 포함되어 있을 수 있음(추후 확장 필요)")

    return out


# ---- optional local smoke test (직접 실행 시) ----
if __name__ == "__main__":
    sample = """
    기준 중위소득 150% 이하
    도시근로자 월평균소득 120% 이하
    연소득 6,000만원 이하
    월 소득 300만원 미만
    5분위
    """
    from pprint import pprint
    pprint(parse_income(sample))