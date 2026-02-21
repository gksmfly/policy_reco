# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Any, Dict

from .utils import norm_text, to_int_safe, result_template


def parse_age(text: str) -> Dict[str, Any]:
    """
    반환 포맷:
    {
      "entity": "age",
      "constraints": [
        {"type":"min", "value":19},
        {"type":"max", "value":34},
        {"type":"range", "min":19, "max":34},
        {"type":"exact", "value":65},
      ],
      "notes": [...],
      "evidence": [...]
    }
    """
    t = norm_text(text)
    out = result_template("age")
    if not t:
        return out

    # 패턴들
    patterns = [
        # 만 19세 이상 / 19세 이상
        (r"(만\s*)?(\d{1,2})\s*세\s*이상", "min"),
        # 만 34세 이하 / 34세 이하
        (r"(만\s*)?(\d{1,2})\s*세\s*이하", "max"),
        # 만 19세 ~ 34세 / 19세~34세 / 19-34세
        (r"(만\s*)?(\d{1,2})\s*세?\s*(?:~|-|–|—)\s*(만\s*)?(\d{1,2})\s*세", "range"),
        # 65세 (이상/이하 없이 단독은 exact로 두되 note)
        (r"(만\s*)?(\d{1,2})\s*세\b", "maybe_exact"),
    ]

    used_spans = set()

    # range 우선
    for m in re.finditer(patterns[2][0], t, re.IGNORECASE):
        a = to_int_safe(m.group(2))
        b = to_int_safe(m.group(4))
        if a is None or b is None:
            continue
        out["constraints"].append({"type": "range", "min": min(a, b), "max": max(a, b)})
        out["evidence"].append(m.group(0))
        used_spans.add(m.span())

    # min/max
    for pat, typ in [patterns[0], patterns[1]]:
        for m in re.finditer(pat, t, re.IGNORECASE):
            # range에 포함된 span이면 스킵(대충)
            if any(_overlap(m.span(), s) for s in used_spans):
                continue
            v = to_int_safe(m.group(2))
            if v is None:
                continue
            out["constraints"].append({"type": typ, "value": v})
            out["evidence"].append(m.group(0))

    # maybe_exact: 다른 조건이 하나도 없을 때만 참고
    if not out["constraints"]:
        for m in re.finditer(patterns[3][0], t, re.IGNORECASE):
            v = to_int_safe(m.group(2))
            if v is None:
                continue
            out["constraints"].append({"type": "exact", "value": v})
            out["notes"].append("단독 'N세' 표현은 문맥상 정확조건이 아닐 수 있음")
            out["evidence"].append(m.group(0))
            break

    return out


def _overlap(a, b) -> bool:
    return not (a[1] <= b[0] or b[1] <= a[0])