from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


# ----------------------------
# User input schema
# ----------------------------
@dataclass
class UserProfile:
    age: int
    annual_income: Optional[int] = None  # 원 단위 (예: 50_000_000)
    assets: Optional[int] = None         # 원 단위 (예: 200_000_000)
    is_homeless: Optional[bool] = None   # 무주택 여부(True/False)
    vehicle_value: Optional[int] = None  # 차량가액(원 단위)


# ----------------------------
# CSV read (encoding + delimiter fallback)
# ----------------------------
def read_csv_with_fallback(path: str) -> pd.DataFrame:
    """
    - 인코딩: utf-8/utf-8-sig/cp949/euc-kr 순서로 시도
    - 구분자: 탭(TSV) 먼저, 그 다음 콤마(CSV) 시도
    """
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]
    seps = ["\t", ","]

    last_err: Exception | None = None
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep)
                # 잘못 읽힌 경우(컬럼 1개 + 헤더에 탭 포함) 방지
                if len(df.columns) == 1 and ("\t" in str(df.columns[0])):
                    continue

                # 컬럼명 정리
                df.columns = df.columns.astype(str).str.strip()
                print(f"[INFO] Loaded CSV with encoding={enc}, sep={repr(sep)}")
                return df
            except Exception as e:
                last_err = e
                continue

    raise ValueError(f"CSV/TSV 로딩 실패: {last_err}")


# ----------------------------
# Normalizers
# ----------------------------
def _to_bool(v: Any, default: bool = False) -> bool:
    """TRUE/False/1/0/'TRUE'/'FALSE' 등을 안전하게 bool로."""
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return bool(v)
    if isinstance(v, float):
        if math.isnan(v):
            return default
        return bool(int(v))
    if isinstance(v, str):
        s = v.strip().upper()
        if s in ("TRUE", "T", "Y", "YES", "1"):
            return True
        if s in ("FALSE", "F", "N", "NO", "0", ""):
            return False
    return default


def _to_int_or_none(v: Any) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if math.isnan(v):
            return None
        return int(v)
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return None
        s = s.replace(",", "")
        try:
            return int(float(s))
        except ValueError:
            return None
    return None


# ----------------------------
# Eligibility check
# ----------------------------
def check_eligibility(
    policy_row: dict[str, Any],
    user: UserProfile,
) -> tuple[bool, dict[str, list[str]]]:
    """
    policy_row columns expected (policy_eligibility.csv):
      - policy_id
      - min_age, max_age
      - income_rule_type ('AMOUNT'/'MEDIAN_RATIO'/'NONE')
      - income_threshold (annual 기준, 원)
      - asset_threshold (원)
      - is_homeowner_required (TRUE/FALSE)
      - vehicle_value_limit (원)
    """
    passed: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []

    # ---- Age ----
    min_age = _to_int_or_none(policy_row.get("min_age"))
    max_age = _to_int_or_none(policy_row.get("max_age"))

    if min_age is None and max_age is None:
        skipped.append("나이 조건 없음")
    else:
        if min_age is not None and user.age < min_age:
            failed.append(f"나이 미충족: {user.age} < 최소 {min_age}")
        if max_age is not None and user.age > max_age:
            failed.append(f"나이 미충족: {user.age} > 최대 {max_age}")
        if not failed:
            if min_age is not None and max_age is not None:
                passed.append(f"나이 충족: {min_age}~{max_age}")
            elif min_age is not None:
                passed.append(f"나이 충족: {min_age} 이상")
            else:
                passed.append(f"나이 충족: {max_age} 이하")

    # ---- Homeowner / Homeless ----
    homeowner_required = _to_bool(policy_row.get("is_homeowner_required"), default=False)
    if homeowner_required:
        if user.is_homeless is None:
            failed.append("무주택 여부 정보 없음(정책은 무주택 필수)")
        elif user.is_homeless is False:
            failed.append("무주택 조건 미충족(정책은 무주택 필수)")
        else:
            passed.append("무주택 조건 충족")
    else:
        skipped.append("무주택 조건 없음")

    # ---- Income ----
    income_rule_type = (policy_row.get("income_rule_type") or "NONE").strip().upper()
    income_threshold = _to_int_or_none(policy_row.get("income_threshold"))

    if income_rule_type == "NONE":
        skipped.append("소득 조건 없음")
    elif income_rule_type == "MEDIAN_RATIO":
        # 현재 입력(annual_income)만으로는 중위소득% 비교 불가 → MVP에서는 보류 처리
        skipped.append("중위소득(%) 조건: 비교 불가 → 보류")
    elif income_rule_type == "AMOUNT":
        if income_threshold is None:
            skipped.append("소득 AMOUNT 타입이나 threshold 없음(데이터 확인 필요)")
        else:
            if user.annual_income is None:
                failed.append("연소득 정보 없음(정책은 소득 상한 존재)")
            elif user.annual_income > income_threshold:
                failed.append(
                    f"소득 미충족: {user.annual_income:,}원 > 기준 {income_threshold:,}원"
                )
            else:
                passed.append(
                    f"소득 충족: {user.annual_income:,}원 ≤ {income_threshold:,}원"
                )
    else:
        skipped.append(f"소득 조건 타입 미인식({income_rule_type}) → 보류")

    # ---- Assets ----
    asset_threshold = _to_int_or_none(policy_row.get("asset_threshold"))
    if asset_threshold is None:
        skipped.append("자산 조건 없음")
    else:
        if user.assets is None:
            failed.append("자산 정보 없음(정책은 자산 상한 존재)")
        elif user.assets > asset_threshold:
            failed.append(
                f"자산 미충족: {user.assets:,}원 > 기준 {asset_threshold:,}원"
            )
        else:
            passed.append(
                f"자산 충족: {user.assets:,}원 ≤ {asset_threshold:,}원"
            )

    # ---- Vehicle ----
    vehicle_limit = _to_int_or_none(policy_row.get("vehicle_value_limit"))
    if vehicle_limit is None:
        skipped.append("차량가액 조건 없음")
    else:
        if user.vehicle_value is None:
            failed.append("차량가액 정보 없음(정책은 차량 상한 존재)")
        elif user.vehicle_value > vehicle_limit:
            failed.append(
                f"차량가액 미충족: {user.vehicle_value:,}원 > 기준 {vehicle_limit:,}원"
            )
        else:
            passed.append(
                f"차량가액 충족: {user.vehicle_value:,}원 ≤ {vehicle_limit:,}원"
            )

    eligible = len(failed) == 0
    return eligible, {"passed": passed, "failed": failed, "skipped": skipped}


# ----------------------------
# Main filter: input CSV -> output dict
# ----------------------------
def filter_policies_from_csv(
    policy_eligibility_csv_path: str,
    *,
    age: int,
    annual_income: Optional[int] = None,
    assets: Optional[int] = None,
    is_homeless: Optional[bool] = None,
    vehicle_value: Optional[int] = None,
) -> dict[str, Any]:
    """
    Input: policy_eligibility.csv (CSV/TSV)
    Output: user 변수명은 그대로 (age, annual_income, assets) 포함해서 반환
    """
    df = read_csv_with_fallback(policy_eligibility_csv_path)

    required_cols = {
        "policy_id",
        "min_age",
        "max_age",
        "income_rule_type",
        "income_threshold",
        "asset_threshold",
        "is_homeowner_required",
        "vehicle_value_limit",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"policy_eligibility.csv에 필요한 컬럼이 없습니다: {sorted(missing)}")

    user = UserProfile(
        age=age,
        annual_income=annual_income,
        assets=assets,
        is_homeless=is_homeless,
        vehicle_value=vehicle_value,
    )

    passed_policies = []
    failed_policies = []

    for row in df.to_dict(orient="records"):
        ok, explain = check_eligibility(row, user)
        item = {
            "policy_id": row.get("policy_id"),
            "explain": explain,
        }
        if ok:
            passed_policies.append(item)
        else:
            failed_policies.append(item)

    return {
        # ✅ 요구한 user 변수명 그대로 유지
        "age": age,
        "annual_income": annual_income,
        "assets": assets,
        # 추가 입력도 포함(원하면 제거 가능)
        "is_homeless": is_homeless,
        "vehicle_value": vehicle_value,
        "passed": passed_policies,
        "failed": failed_policies,
        "counts": {"passed": len(passed_policies), "failed": len(failed_policies)},
    }


# ----------------------------
# CLI run example
# ----------------------------
if __name__ == "__main__":
    result = filter_policies_from_csv(
        "../../../pipeline/cleaner/policy_eligibility.csv",
        age=31,
        annual_income=50_000_000,
        assets=200_000_000,
        is_homeless=True,
        vehicle_value=38_030_000,  # 예: 38,030,000원
    )

    print("\n=== FILTER RESULT SUMMARY ===")
    print("age:", result["age"])
    print("annual_income:", result["annual_income"])
    print("assets:", result["assets"])
    print("vehicle_value:", result["vehicle_value"])
    print("passed:", result["counts"]["passed"], "failed:", result["counts"]["failed"])

    for i, p in enumerate(result["passed"][:5], 1):
        print(f"\n--- PASS #{i} policy_id={p['policy_id']} ---")
        print("passed:", p["explain"]["passed"])
        print("skipped:", p["explain"]["skipped"])