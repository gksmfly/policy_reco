# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import Any, Dict, List

MISSING_VALUE = "__MISSING__"

MAX_LINES = {
    "summary": 2,
    "target": 4,
    "elig": 5,
    "benefit": 6,
    "apply": 6,
    "period": 2,
}

WRAP_AT = 85


# -------------------------
# basic clean
# -------------------------
def _clean(v: Any) -> str:
    if v is None:
        return ""
    s = str(v).replace("\r", "\n").strip()
    if not s or s.lower() == "nan" or s == MISSING_VALUE:
        return ""
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _strip_marker(s: str) -> str:
    s = re.sub(r"^\s*[•·○●■□\-–—\*]+\s*", "", s)
    s = re.sub(r"^\s*↳\s*", "", s)
    s = re.sub(r"^\s*※\s*", "", s)
    return s.strip()


def _is_noise(line: str) -> bool:
    s = line.strip()
    if not s:
        return True

    # 조건/표/숫자 나열 제거
    if re.search(r"\d+\s*(만원|원|%|㎡|m2|m²)", s):
        return True
    if re.search(r"\d+\s*[-~]\s*\d+", s):
        return True
    if s.count("/") >= 2:
        return True
    if sum(c.isdigit() for c in s) > 6:
        return True

    noisy = [
        "임대조건", "지원한도", "지원금리",
        "수도권", "광역시", "도(道)지역",
        "총자산", "자동차"
    ]
    if any(k in s for k in noisy):
        return True

    return False


def _wrap(line: str) -> List[str]:
    if len(line) <= WRAP_AT:
        return [line]
    line = re.sub(r"([\.!?])\s+", r"\1\n", line)
    return [x.strip() for x in line.split("\n") if x.strip()]


def _block(text: Any, max_lines: int) -> str:
    t = _clean(text)
    if not t:
        return ""

    out = []
    for ln in t.splitlines():
        ln = _strip_marker(ln)
        if not ln or _is_noise(ln):
            continue
        out.extend(_wrap(ln))

    # 중복 제거
    uniq = []
    seen = set()
    for ln in out:
        if ln not in seen:
            seen.add(ln)
            uniq.append(ln)

    return "\n".join(uniq[:max_lines]).strip()


# -------------------------
# summary fallback
# -------------------------
def _build_summary(row: Dict[str, Any]) -> str:
    summary = _block(row.get("support_summary"), MAX_LINES["summary"])
    if summary:
        return summary

    # fallback 1
    summary = _block(row.get("benefit"), 1)
    if summary:
        return summary

    # fallback 2
    summary = _block(row.get("support_detail"), 1)
    return summary


# -------------------------
# apply formatting
# -------------------------
def _format_apply(text: Any) -> str:
    t = _clean(text)
    if not t:
        return ""

    lines = [x.strip() for x in t.splitlines() if x.strip()]
    out = []
    i = 0

    while i < len(lines):
        m = re.match(r"(?i)^step\s*(\d+)", lines[i])
        if m and i + 1 < len(lines):
            desc = _strip_marker(lines[i + 1])
            out.append(f"{m.group(1)}. {desc}")
            i += 2
        else:
            out.append(_strip_marker(lines[i]))
            i += 1

    return _block("\n".join(out), MAX_LINES["apply"])


def _extract_phone(row: Dict[str, Any]) -> str:
    blob = "\n".join([
        _clean(row.get("apply_process")),
        _clean(row.get("support_detail")),
        _clean(row.get("eligibility"))
    ])
    phones = re.findall(r"(?:0\d{1,2})[- ]?\d{3,4}[- ]?\d{4}", blob)
    return phones[0] if phones else ""


def _extract_url(row: Dict[str, Any]) -> str:
    for k in ["source_url", "detail_url", "url"]:
        v = _clean(row.get(k))
        if v.startswith("http"):
            return v
    return ""


# -------------------------
# main
# -------------------------
def build_clean_text(row: Dict[str, Any], *, max_chars: int = 1500) -> str:
    parts = []

    # 0) 제목 + 요약
    name = _clean(row.get("policy_name"))
    summary = _build_summary(row)

    if name:
        parts.append(f"[{name}]")
    if summary:
        parts.append(summary)

    # 1) 지원 대상 / 자격
    target = _block(row.get("eligibility"), MAX_LINES["target"])
    if target:
        parts.append("* 지원 대상\n" + target)

    elig = _block(row.get("eligibility"), MAX_LINES["elig"])
    if elig:
        parts.append("* 지원 자격\n" + elig)

    # 2) 지원 내용
    benefit = _block(row.get("benefit") or row.get("support_detail"), MAX_LINES["benefit"])
    if benefit:
        parts.append("* 지원 내용\n" + benefit)

    # 3) 신청 방법
    apply = _format_apply(row.get("apply_process"))
    if apply:
        parts.append("신청 방법\n" + apply)

    # 4) 신청 기간
    period = _block(row.get("apply_period"), MAX_LINES["period"])
    if period:
        parts.append("* 신청 기간\n" + period)

    # 5) 문의처
    phone = _extract_phone(row)
    if phone:
        parts.append("문의처\n" + phone)

    # 6) 링크
    url = _extract_url(row)
    if url:
        parts.append(f"정책 설명 전문 보러가기 → {url}")

    text = "\n\n".join(parts).strip()

    if len(text) > max_chars:
        text = text[:max_chars].rstrip()

    return text