# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, List

import pandas as pd


# -------------------------
# logger
# -------------------------
def setup_logger(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("cleaner")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    fmt = logging.Formatter("[%(levelname)s] %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger


# -------------------------
# missing / text utils
# -------------------------
def _is_missing(v: Any) -> bool:
    """결측 판단: None, pandas NA/NaN, 빈 문자열, 'nan', (혹시 남아있을) '__MISSING__'"""
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except Exception:
        pass
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return True
        if s.lower() == "nan":
            return True
        if s == "__MISSING__":  # 과거 데이터 방어
            return True
    return False


def _to_text(v: Any) -> str:
    """결측이면 '' 반환, 아니면 문자열로 정리"""
    if _is_missing(v):
        return ""
    s = str(v)
    s = s.replace("\r\n", "\n").replace("\r", "\n").strip()
    # 가벼운 공백 정리(줄바꿈은 유지)
    if "\n" in s:
        s = "\n".join([" ".join(line.split()) for line in s.split("\n")]).strip()
    else:
        s = " ".join(s.split()).strip()
    return s


# -------------------------
# 계약 검증 (fail-fast)
# -------------------------
def validate_input_contract(df: pd.DataFrame) -> None:
    """
    [무조건 계약 준수]
    - policy_id 컬럼 존재 + 값 비어있으면 안됨 + 중복 불가
    - eligibility 컬럼 존재 + 값 비어있으면 안됨
    """
    required_cols = ["policy_id", "eligibility"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Schema violation: missing required columns: {missing}")

    pid = df["policy_id"].astype(str).str.strip()
    if (pid == "").any():
        raise ValueError("Schema violation: policy_id contains empty values")
    if pid.duplicated(keep=False).any():
        top = pid[pid.duplicated(keep=False)].value_counts().head(10).to_dict()
        raise ValueError(f"Schema violation: duplicated policy_id exists (top10): {top}")

    elig = df["eligibility"].astype(str).str.strip()
    if (elig == "").any():
        cnt = int((elig == "").sum())
        raise ValueError(f"Schema violation: eligibility contains empty values (count={cnt})")


# -------------------------
# safe import (rules/build_clean_text)
# -------------------------
def safe_import_rules(logger: logging.Logger):
    try:
        from pipeline.cleaner.rules.parse_age import parse_age
    except Exception as e:
        logger.warning(f"parse_age not found → noop 사용 ({e})")
        parse_age = lambda *args, **kwargs: {}

    try:
        from pipeline.cleaner.rules.parse_income import parse_income
    except Exception as e:
        logger.warning(f"parse_income not found → noop 사용 ({e})")
        parse_income = lambda *args, **kwargs: {}

    try:
        from pipeline.cleaner.rules.parse_assets import parse_assets
    except Exception as e:
        logger.warning(f"parse_assets not found → noop 사용 ({e})")
        parse_assets = lambda *args, **kwargs: {}

    try:
        from pipeline.cleaner.rules.parse_car import parse_car
    except Exception as e:
        logger.warning(f"parse_car not found → noop 사용 ({e})")
        parse_car = lambda *args, **kwargs: {}

    return parse_age, parse_income, parse_assets, parse_car


def safe_import_build_clean_text(logger: logging.Logger):
    """
    1) 정상 패키지 import: pipeline.cleaner.build_clean_text
    2) 실패하면, 현재 파일 기준 동일 폴더의 build_clean_text.py 직접 로드(importlib)
    3) 그래도 실패하면 fallback
    """
    try:
        from pipeline.cleaner.build_clean_text import build_clean_text
        logger.info("build_clean_text loaded (package import)")
        return build_clean_text
    except Exception as e1:
        logger.warning(f"build_clean_text package import failed: {e1}")

    # direct load next to this file
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(here, "build_clean_text.py")
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location("build_clean_text_local", module_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                build_clean_text = getattr(mod, "build_clean_text")
                logger.info("build_clean_text loaded (direct file import)")
                return build_clean_text
        logger.warning("build_clean_text.py not found next to run_clean.py")
    except Exception as e2:
        logger.warning(f"build_clean_text direct import failed: {e2}")

    logger.warning("build_clean_text not found → fallback 사용")

    def fallback(row: Dict[str, Any], max_chars: int = 6000):
        parts: List[str] = []
        for k in ("policy_name", "support_summary", "eligibility", "support_detail"):
            v = _to_text(row.get(k))
            if v:
                parts.append(f"[{k}]\n{v}")
        raw = _to_text(row.get("raw_text"))
        if raw:
            parts.append(f"[raw]\n{raw[:2000]}")
        text = "\n\n".join(parts)
        return text[:max_chars]

    return fallback


# -------------------------
# helpers: parsing normalization to DB contract
# -------------------------
def _constraints(obj: Any) -> List[dict]:
    if isinstance(obj, dict) and isinstance(obj.get("constraints"), list):
        return [c for c in obj["constraints"] if isinstance(c, dict)]
    return []


def pick_age_min_max(age_obj: Any) -> Tuple[Optional[int], Optional[int]]:
    """
    age_obj.constraints format expected (from parse_age):
      - {"type":"range","min":..,"max":..}
      - {"type":"min","value":..}
      - {"type":"max","value":..}
    """
    mn: Optional[int] = None
    mx: Optional[int] = None

    for c in _constraints(age_obj):
        t = c.get("type")
        if t == "range":
            a = c.get("min")
            b = c.get("max")
            if isinstance(a, (int, float)):
                mn = int(a) if mn is None else min(mn, int(a))
            if isinstance(b, (int, float)):
                mx = int(b) if mx is None else max(mx, int(b))
        elif t == "min":
            v = c.get("value")
            if isinstance(v, (int, float)):
                mn = int(v) if mn is None else min(mn, int(v))
        elif t == "max":
            v = c.get("value")
            if isinstance(v, (int, float)):
                mx = int(v) if mx is None else max(mx, int(v))

    return mn, mx


def pick_min_of_type(obj: Any, type_keys: Tuple[str, ...]) -> Optional[int]:
    """상한류(최대값 제한)는 가장 타이트한 값 = min(value) 선택"""
    vals: List[int] = []
    for c in _constraints(obj):
        if c.get("type") in type_keys:
            v = c.get("value")
            if isinstance(v, (int, float)):
                vals.append(int(v))
    return min(vals) if vals else None


def normalize_income_to_contract(income_obj: Any, logger: logging.Logger) -> Tuple[str, Optional[int]]:
    """
    계약 enum: NONE | AMOUNT | MEDIAN_RATIO
    계약 income_threshold: 원 단위, 연소득 기준 (AMOUNT일 때만 채움)

    우선순위(계약 맞춤):
    1) 중위소득% 조건이 있으면 -> MEDIAN_RATIO, threshold = None
    2) 연소득 상한이 있으면 -> AMOUNT, threshold = 연소득(원)
    3) 월소득 상한이 있으면 -> AMOUNT, threshold = 월소득(원) * 12
    4) 그 외 -> NONE
    """
    cs = _constraints(income_obj)
    types = {c.get("type") for c in cs}

    # 1) median ratio
    if "median_percent_max" in types or "median_percent_min" in types:
        return "MEDIAN_RATIO", None

    # 2) annual max (choose tightest)
    annual = pick_min_of_type(income_obj, ("annual_max_won",))
    if annual is not None:
        return "AMOUNT", int(annual)

    # 3) monthly max -> annualize
    monthly = pick_min_of_type(income_obj, ("monthly_max_won",))
    if monthly is not None:
        # 계약: 연소득 기준 고정
        return "AMOUNT", int(monthly) * 12

    # (참고) min bound만 있는 경우(rare): 계약에 맞추기 애매하므로 NONE 처리
    if "annual_min_won" in types or "monthly_min_won" in types:
        logger.warning("income has only MIN-type constraints (annual_min_won/monthly_min_won). "
                       "Contract supports threshold as eligibility upper bound; set income_rule_type=NONE.")
        return "NONE", None

    return "NONE", None


def infer_is_homeowner_required(text: str) -> bool:
    """
    계약 필드명은 is_homeowner_required지만,
    실제 의미는 '주택 소유자여야 함'보다는 정책에서 '무주택'을 요구하는 경우가 많음.
    여기서는 텍스트에 '무주택/주택 미소유'가 있으면 True로 둔다.
    (팀이 의미를 '무주택 required'로 쓰는지 확정 필요. 계약을 바꾸지 못한다면, 이 로직이 표준이 됨.)
    """
    t = text or ""
    return bool(re.search(r"(무주택|주택\s*미소유|주택\s*소유\s*불가|자가\s*없)", t))


# -------------------------
# policies field mapping (input -> contract)
# -------------------------
def build_support_summary(row: Dict[str, Any]) -> str:
    # 계약: support_summary(짧은 요약)
    # 입력이 summary/support_summary 둘 중 하나일 수 있으니 fallback 처리
    v = _to_text(row.get("support_summary"))
    if v:
        return v
    v = _to_text(row.get("summary"))
    if v:
        return v
    # 최후: benefit/eligibility 일부로 생성
    elig = _to_text(row.get("eligibility"))
    ben = _to_text(row.get("benefit"))
    base = " / ".join([x for x in [elig[:80], ben[:80]] if x])
    return base[:200]  # 짧게 제한


def build_support_detail(row: Dict[str, Any]) -> str:
    # 계약: support_detail(상세)
    v = _to_text(row.get("support_detail"))
    if v:
        return v
    # raw_text가 있으면 raw_text 우선
    raw = _to_text(row.get("raw_text"))
    if raw:
        return raw
    # 최후: 구조화 필드 합성
    parts: List[str] = []
    for k in ("eligibility", "benefit", "apply_process", "apply_period"):
        txt = _to_text(row.get(k))
        if txt:
            parts.append(f"[{k}]\n{txt}")
    return "\n\n".join(parts).strip()


# -------------------------
# core
# -------------------------
def run_clean(input_csv: str, limit: Optional[int] = None, verbose: bool = False) -> None:
    logger = setup_logger(verbose)

    df = pd.read_csv(input_csv, encoding="utf-8-sig")
    validate_input_contract(df)

    if limit:
        df = df.head(limit)

    parse_age, parse_income, parse_assets, parse_car = safe_import_rules(logger)
    build_clean_text = safe_import_build_clean_text(logger)

    # output rows
    policies_rows: List[Dict[str, Any]] = []
    elig_rows: List[Dict[str, Any]] = []

    now_iso = datetime.now(timezone.utc).isoformat()

    for _, r in df.iterrows():
        row = r.to_dict()

        policy_id = _to_text(row.get("policy_id"))
        # policy_name 계약 필수: 없으면 에러
        policy_name = _to_text(row.get("policy_name"))
        if not policy_name:
            raise ValueError(f"Schema violation: policy_name is required for policies (policy_id={policy_id})")

        # rules input text (결측 제외)
        chunks = [
            _to_text(row.get("eligibility")),
            _to_text(row.get("benefit")),
            _to_text(row.get("apply_process")),
            _to_text(row.get("apply_period")),
            _to_text(row.get("raw_text")),
        ]
        text_for_rules = "\n".join([c for c in chunks if c])

        age_obj = parse_age(text_for_rules)
        income_obj = parse_income(text_for_rules)
        assets_obj = parse_assets(text_for_rules)
        car_obj = parse_car(text_for_rules)

        min_age, max_age = pick_age_min_max(age_obj)
        income_rule_type, income_threshold = normalize_income_to_contract(income_obj, logger)

        # 계약: asset_threshold, vehicle_value_limit은 단일 원 값 (없으면 null)
        # parse_assets: {"type":"max_won","value":...} 같은 형태를 기대
        asset_threshold = pick_min_of_type(assets_obj, ("max_won", "asset_max_won", "assets_max_won"))
        # parse_car: {"type":"value_max_won","value":...} 또는 {"type":"max_won","value":...} 가능
        vehicle_value_limit = pick_min_of_type(car_obj, ("value_max_won", "car_value_max_won", "max_won"))

        is_homeowner_required = bool(infer_is_homeowner_required(text_for_rules))

        # clean_text 생성(결측은 제외된 상태로 builder가 처리해야 함)
        # build_clean_text는 row dict를 받으므로, 계약명 컬럼도 함께 넣어주는게 안전
        # (builder가 summary를 쓰는 경우를 위해 summary/support_summary 모두 노출)
        row_for_clean = dict(row)
        row_for_clean["support_summary"] = build_support_summary(row)
        row_for_clean["support_detail"] = build_support_detail(row)
        clean_text = build_clean_text(row_for_clean)

        # region (nullable)
        region = row.get("region", pd.NA)
        if _is_missing(region):
            region = pd.NA
        else:
            region = _to_text(region)

        # policies (2.2) row
        policies_rows.append(
            {
                "policy_id": policy_id,
                "policy_name": policy_name,
                "support_summary": build_support_summary(row),
                "support_detail": build_support_detail(row),
                "region": region,  # nullable
                "clean_text": clean_text,
                "updated_at": now_iso,
            }
        )

        # policy_eligibility (2.3) row
        elig_rows.append(
            {
                "policy_id": policy_id,
                "min_age": min_age,
                "max_age": max_age,
                "income_rule_type": income_rule_type,        # NONE/AMOUNT/MEDIAN_RATIO
                "income_threshold": income_threshold,        # AMOUNT일 때만 값(연소득 원)
                "asset_threshold": asset_threshold,          # 원
                "is_homeowner_required": bool(is_homeowner_required),
                "vehicle_value_limit": vehicle_value_limit,  # 원
            }
        )

    policies_df = pd.DataFrame(policies_rows)
    elig_df = pd.DataFrame(elig_rows)

    # output path (always cleaner dir)
    cleaner_dir = os.path.dirname(os.path.abspath(__file__))
    policies_out = os.path.join(cleaner_dir, "policies.csv")
    elig_out = os.path.join(cleaner_dir, "policy_eligibility.csv")

    # 계약 컬럼 순서 강제
    policies_cols = [
        "policy_id",
        "policy_name",
        "support_summary",
        "support_detail",
        "region",
        "clean_text",
        "updated_at",
    ]
    elig_cols = [
        "policy_id",
        "min_age",
        "max_age",
        "income_rule_type",
        "income_threshold",
        "asset_threshold",
        "is_homeowner_required",
        "vehicle_value_limit",
    ]
    policies_df = policies_df[policies_cols]
    elig_df = elig_df[elig_cols]

    # income_rule_type 유효성 최종 체크(fail-fast)
    allowed = {"NONE", "AMOUNT", "MEDIAN_RATIO"}
    bad = set(policies_df.columns)  # dummy to quiet linters
    bad = set(elig_df["income_rule_type"].dropna().astype(str)) - allowed
    if bad:
        raise ValueError(f"Contract violation: invalid income_rule_type values found: {sorted(list(bad))}")

    try:
        policies_df.to_csv(policies_out, index=False, encoding="utf-8-sig")
        elig_df.to_csv(elig_out, index=False, encoding="utf-8-sig")
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied while writing outputs in: {cleaner_dir}\n"
            f"- 파일이 엑셀/편집기에서 열려있으면 닫고 다시 실행\n"
            f"- 또는 기존 파일 삭제/이름변경 후 재실행\n"
            f"Original error: {e}"
        )

    logger.info(f"Saved → {policies_out}")
    logger.info(f"Saved → {elig_out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="input policies.csv path")
    ap.add_argument("--limit", type=int, help="optional: process only first N rows")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    run_clean(
        input_csv=args.input,
        limit=args.limit,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()