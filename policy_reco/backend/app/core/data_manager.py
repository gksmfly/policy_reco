from __future__ import annotations

import os
from functools import lru_cache
from typing import Tuple

import pandas as pd


def _read_csv_with_fallback(path: str, *, prefer_sep: str | None = None) -> pd.DataFrame:
    """
    - 인코딩: utf-8/utf-8-sig/cp949/euc-kr 순서로 시도
    - 구분자: prefer_sep가 있으면 우선 사용, 그 다음 '\t'와 ','를 시도
    """
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr"]
    seps = []
    if prefer_sep:
        seps.append(prefer_sep)
    for s in ["\t", ","]:
        if s not in seps:
            seps.append(s)

    last_err: Exception | None = None
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep)
                # 잘못 읽힌 경우 방지:
                # - 탭으로 읽었는데 컬럼이 1개면(대부분 CSV를 잘못 읽은 것) 스킵
                if sep == "\t" and len(df.columns) == 1:
                    continue
                # - 컬럼 1개인데 헤더에 탭이 섞여있으면 잘못 읽힌 것
                if len(df.columns) == 1 and ("\t" in str(df.columns[0])):
                    continue
                df.columns = df.columns.astype(str).str.strip()
                return df
            except Exception as e:
                last_err = e
                continue

    raise ValueError(f"CSV/TSV 로딩 실패: {path} ({last_err})")


def _project_root() -> str:
    # backend/app/core/data_manager.py 기준 -> policy_reco/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _csv_paths() -> Tuple[str, str]:
    root = _project_root()
    policies_csv = os.path.join(root, "pipeline", "cleaner", "policies.csv")
    eligibility_csv = os.path.join(root, "pipeline", "cleaner", "policy_eligibility.csv")
    return policies_csv, eligibility_csv


@lru_cache(maxsize=1)
def get_dataframes() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    서버 프로세스에서 1회만 로드해 메모리에 유지.
    """
    policies_csv, eligibility_csv = _csv_paths()

    if not os.path.exists(policies_csv):
        raise FileNotFoundError(f"policies.csv not found: {policies_csv}")
    if not os.path.exists(eligibility_csv):
        raise FileNotFoundError(f"policy_eligibility.csv not found: {eligibility_csv}")

    # policies.csv는 일반 CSV가 대부분이라 ','를 우선
    policies_df = _read_csv_with_fallback(policies_csv, prefer_sep=",")
    eligibility_df = _read_csv_with_fallback(eligibility_csv, prefer_sep="\t")

    # eligibility가 한 컬럼으로 들어온 경우(헤더에 탭이 있거나) 재파싱
    if len(eligibility_df.columns) == 1 and "\t" in eligibility_df.columns[0]:
        col = eligibility_df.columns[0]
        cols = [c.strip() for c in col.split("\t")]
        values = eligibility_df[col].astype(str).str.split("\t", expand=True)
        values.columns = cols
        eligibility_df = values

    # 공통적으로 policy_id는 int로 맞춰준다(조인/검색 안정)
    if "policy_id" in policies_df.columns:
        policies_df["policy_id"] = pd.to_numeric(policies_df["policy_id"], errors="coerce").astype("Int64")
    if "policy_id" in eligibility_df.columns:
        eligibility_df["policy_id"] = pd.to_numeric(eligibility_df["policy_id"], errors="coerce").astype("Int64")

    return policies_df, eligibility_df


def get_csv_paths() -> Tuple[str, str]:
    return _csv_paths()
