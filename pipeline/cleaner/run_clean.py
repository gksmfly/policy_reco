# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import importlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, List

import pandas as pd

import sys
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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
    """결측 판단: None, pandas NA/NaN, 빈 문자열, 'nan', '__MISSING__'"""
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
        if s == "__MISSING__":
            return True
    return False


def _to_text(v: Any) -> str:
    """결측이면 '' 반환, 아니면 문자열로 정리"""
    if _is_missing(v):
        return ""
    s = str(v)
    s = s.replace("\r\n", "\n").replace("\r", "\n").strip()
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
    입력 최소 계약:
    - policy_id 컬럼 존재 + 값 비어있으면 안됨 (중복 허용: 출력에서 재번호 부여하므로)
    - eligibility 컬럼 존재 + 값 비어있으면 안됨
    """
    required_cols = ["policy_id", "eligibility"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Schema violation: missing required columns: {missing}")

    pid = df["policy_id"].astype(str).str.strip()
    if (pid == "").any():
        raise ValueError("Schema violation: policy_id contains empty values")

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
    3) 그래도 실패하면 fallback (포맷 고정 버전)
    """
    try:
        from pipeline.cleaner.build_clean_text import build_clean_text
        logger.info("build_clean_text loaded (package import)")
        return build_clean_text
    except Exception as e1:
        logger.warning(f"build_clean_text package import failed: {e1}")

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

    logger.warning("build_clean_text not found → fallback 사용 (포맷 고정)")

    def fallback(row: Dict[str, Any], max_chars: int = 2500):
        # 요구 포맷(최소)만 보장하는 fallback
        policy_name = _to_text(row.get("policy_name"))
        summary = _to_text(row.get("support_summary") or row.get("summary"))

        parts: List[str] = []
        basic = "\n".join([x for x in [policy_name, f"요약: {summary}" if summary else ""] if x]).strip()
        if basic:
            parts.append("[기본]\n" + basic)

        for title, key in [
            ("사업 개요", "support_detail"),
            ("지원 대상", "eligibility"),
            ("신청 방법", "apply_process"),
            ("지원 내용", "benefit"),
            ("문의처", "contact"),
        ]:
            v = _to_text(row.get(key))
            if v:
                parts.append(f"[{title}]\n{v}")

        text = "\n\n".join(parts).strip()
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
    vals: List[int] = []
    for c in _constraints(obj):
        if c.get("type") in type_keys:
            v = c.get("value")
            if isinstance(v, (int, float)):
                vals.append(int(v))
    return min(vals) if vals else None


def normalize_income_to_contract(income_obj: Any, logger: logging.Logger) -> Tuple[str, Optional[int]]:
    cs = _constraints(income_obj)
    types = {c.get("type") for c in cs}

    if "median_percent_max" in types or "median_percent_min" in types:
        return "MEDIAN_RATIO", None

    annual = pick_min_of_type(income_obj, ("annual_max_won",))
    if annual is not None:
        return "AMOUNT", int(annual)

    monthly = pick_min_of_type(income_obj, ("monthly_max_won",))
    if monthly is not None:
        return "AMOUNT", int(monthly) * 12

    if "annual_min_won" in types or "monthly_min_won" in types:
        logger.warning(
            "income has only MIN-type constraints (annual_min_won/monthly_min_won). "
            "Contract supports threshold as eligibility upper bound; set income_rule_type=NONE."
        )
        return "NONE", None

    return "NONE", None


def infer_is_homeowner_required(text: str) -> bool:
    t = text or ""
    return bool(re.search(r"(무주택|주택\s*미소유|주택\s*소유\s*불가|자가\s*없)", t))


# -------------------------
# policies field mapping (input -> contract)
# -------------------------
def build_support_summary(row: Dict[str, Any]) -> str:
    v = _to_text(row.get("support_summary"))
    if v:
        return v
    v = _to_text(row.get("summary"))
    if v:
        return v
    elig = _to_text(row.get("eligibility"))
    ben = _to_text(row.get("benefit"))
    base = " / ".join([x for x in [elig[:80], ben[:80]] if x])
    return base[:200]


def build_support_detail(row: Dict[str, Any]) -> str:
    v = _to_text(row.get("support_detail"))
    if v:
        return v

    label_map = {
        "eligibility": "지원 대상",
        "benefit": "지원 내용",
        # "apply_process": "신청 방법",   # ✅ 제거
        # "apply_period": "신청 기간",   # ✅ 제거
    }

    parts: List[str] = []
    summ = _to_text(row.get("support_summary")) or _to_text(row.get("summary"))
    if summ:
        parts.append(summ)

    # ✅ 여기서도 신청 관련 필드는 제외
    for k in ("eligibility", "benefit"):
        txt = _to_text(row.get(k))
        if txt:
            parts.append(f"■ {label_map.get(k, k)}\n{txt}")

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

    policies_rows: List[Dict[str, Any]] = []
    elig_rows: List[Dict[str, Any]] = []

    now_iso = datetime.now(timezone.utc).isoformat()

    # ✅ 출력 policy_id: 입력의 policy_id와 무관하게 1..N 재번호
    for new_id, r in enumerate(df.itertuples(index=False), start=1):
        row = r._asdict()
        policy_id = int(new_id)

        policy_name = _to_text(row.get("policy_name"))
        if not policy_name:
            raise ValueError(f"Schema violation: policy_name is required for policies (row_new_id={policy_id})")

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

        asset_threshold = pick_min_of_type(assets_obj, ("max_won", "asset_max_won", "assets_max_won"))
        vehicle_value_limit = pick_min_of_type(car_obj, ("value_max_won", "car_value_max_won", "max_won"))
        is_homeowner_required = bool(infer_is_homeowner_required(text_for_rules))

        region = row.get("region", pd.NA)
        if _is_missing(region):
            region = pd.NA
        else:
            region = _to_text(region)

        # ✅ clean_text 입력용 row 만들기
        row_for_clean = dict(row)
        row_for_clean["support_summary"] = build_support_summary(row)
        row_for_clean["support_detail"] = build_support_detail(row)

        # ✅ 문의처 링크 추출용: 원본에 link/source_url 있으면 전달
        if "link" in row and _is_missing(row_for_clean.get("link")):
            row_for_clean["link"] = row.get("link")
        if "source_url" in row and _is_missing(row_for_clean.get("source_url")):
            row_for_clean["source_url"] = row.get("source_url")

        # ✅ 핵심: clean_text에서 raw_text 노이즈를 원천 차단
        row_for_clean["raw_text"] = ""

        clean_text = build_clean_text(row_for_clean)

        policies_rows.append(
            {
                "policy_id": policy_id,
                "policy_name": policy_name,
                "support_summary": row_for_clean["support_summary"],
                "support_detail": row_for_clean["support_detail"],
                "region": region,
                "clean_text": clean_text,
                "updated_at": now_iso,
            }
        )

        elig_rows.append(
            {
                "policy_id": policy_id,
                "min_age": min_age,
                "max_age": max_age,
                "income_rule_type": income_rule_type,  # NONE/AMOUNT/MEDIAN_RATIO
                "income_threshold": income_threshold,  # AMOUNT일 때만 값(연소득 원)
                "asset_threshold": asset_threshold,  # 원
                "is_homeowner_required": bool(is_homeowner_required),
                "vehicle_value_limit": vehicle_value_limit,  # 원
            }
        )

    policies_df = pd.DataFrame(policies_rows)
    elig_df = pd.DataFrame(elig_rows)

    cleaner_dir = os.path.dirname(os.path.abspath(__file__))
    policies_out = os.path.join(cleaner_dir, "policies.csv")
    elig_out = os.path.join(cleaner_dir, "policy_eligibility.csv")
    duplicates_out = os.path.join(cleaner_dir, "duplicates_removed.csv")

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

    allowed = {"NONE", "AMOUNT", "MEDIAN_RATIO"}
    bad = set(elig_df["income_rule_type"].dropna().astype(str)) - allowed
    if bad:
        raise ValueError(f"Contract violation: invalid income_rule_type values found: {sorted(list(bad))}")

    # -------------------------
    # 🔥 내용 기준 중복 제거 + 제거된 목록 저장 + eligibility 동기화
    # -------------------------
    dedup_keys = ["policy_name", "region", "support_summary", "clean_text"]

    policies_df["_kept_policy_id"] = policies_df.groupby(dedup_keys, dropna=False)["policy_id"].transform("first")
    dup_mask = policies_df.duplicated(subset=dedup_keys, keep="first")

    removed_df = policies_df.loc[dup_mask].copy()
    kept_df = policies_df.loc[~dup_mask].copy()

    if not removed_df.empty:
        removed_df = removed_df.rename(columns={"_kept_policy_id": "kept_policy_id"})
        save_cols = ["policy_id", "kept_policy_id"] + dedup_keys + ["updated_at"]
        save_cols = [c for c in save_cols if c in removed_df.columns]
        removed_df[save_cols].to_csv(duplicates_out, index=False, encoding="utf-8-sig")
        logger.info(f"Duplicates removed: {int(dup_mask.sum())}")
        logger.info(f"Saved removed duplicates → {duplicates_out}")
    else:
        logger.info("Duplicates removed: 0")

    policies_df = kept_df.drop(columns=["_kept_policy_id"])

    keep_ids = set(policies_df["policy_id"].tolist())
    elig_df = elig_df[elig_df["policy_id"].isin(keep_ids)].copy()

    if policies_df["policy_id"].duplicated().any():
        raise ValueError("Internal error: duplicated policy_id after renumbering/dedup")

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