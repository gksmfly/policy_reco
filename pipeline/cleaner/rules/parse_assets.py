# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Any, Dict

from .utils import norm_text, parse_money_to_won, result_template


def parse_assets(text: str) -> Dict[str, Any]:
    """
    자산: '총자산/재산/순자산' 상한 중심.
    """
    t = norm_text(text)
    out = result_template("assets")
    if not t:
        return out

    # 예: 총자산 3억원 이하 / 재산 2억 이하 / 순자산 5천만원 미만
    for m in re.finditer(
        r"(총\s*자산|순\s*자산|재산)\s*([0-9][0-9, ]*(?:억|만|원|만원)?)\s*(이하|미만)",
        t,
        re.IGNORECASE,
    ):
        label = m.group(1).replace(" ", "")
        money = m.group(2)
        won = parse_money_to_won(money)
        if won is None:
            # "3억원" 같은 케이스: 숫자+억+원 혼합 방어
            won = parse_money_to_won(money.replace("원", ""))
        if won is None:
            continue
        out["constraints"].append({"type": "max_won", "value": won, "field": label})
        out["evidence"].append(m.group(0))

    return out