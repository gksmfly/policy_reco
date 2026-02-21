# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Any, Dict

from .utils import norm_text, parse_money_to_won, result_template


def parse_car(text: str) -> Dict[str, Any]:
    """
    차량: '차량가액/자동차가액' 상한, '차량 미보유' 등.
    """
    t = norm_text(text)
    out = result_template("car")
    if not t:
        return out

    # 미보유/무소유
    for m in re.finditer(r"(차량|자동차)\s*(미보유|무소유)", t, re.IGNORECASE):
        out["constraints"].append({"type": "must_not_own", "value": True})
        out["evidence"].append(m.group(0))

    # 차량가액 N 이하/미만
    for m in re.finditer(
        r"(차량\s*가액|자동차\s*가액|차량가액|자동차가액)\s*([0-9][0-9, ]*(?:억|만|원|만원)?)\s*(이하|미만)",
        t,
        re.IGNORECASE,
    ):
        money = m.group(2)
        won = parse_money_to_won(money)
        if won is None:
            won = parse_money_to_won(money.replace("원", ""))
        if won is None:
            continue
        out["constraints"].append({"type": "value_max_won", "value": won})
        out["evidence"].append(m.group(0))

    return out