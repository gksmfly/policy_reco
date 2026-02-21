# ingest_raw_policies.py
# ------------------------------------------------------------
# 실행:
#   python ingest_raw_policies.py --csv merged_policies.csv --db policies.db
# ------------------------------------------------------------

from __future__ import annotations

import argparse
import sqlite3
import time
import random

import pandas as pd

from parser import parse_policy_page
from raw_store import upsert_raw_policy


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to merged_policies.csv")
    ap.add_argument("--db", required=True, help="Path to sqlite database file (e.g., policies.db)")
    ap.add_argument("--min-sleep", type=float, default=0.8)
    ap.add_argument("--max-sleep", type=float, default=1.6)
    ap.add_argument("--max-retries", type=int, default=3)
    return ap.parse_args()


def safe_get(row, col: str) -> str:
    v = row.get(col, "")
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def main() -> None:
    args = parse_args()

    df = pd.read_csv(args.csv, encoding="utf-8-sig")

    conn = sqlite3.connect(args.db)

    total = len(df)
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        link = safe_get(row, "link") or safe_get(row, "링크")
        if not link:
            print(f"[{i}/{total}] skip: empty link")
            continue

        policy_name = safe_get(row, "policy_name") or safe_get(row, "정책명")
        target_group = safe_get(row, "target_group") or safe_get(row, "대상")
        summary = safe_get(row, "summary") or safe_get(row, "요약")

        print(f"[{i}/{total}] Fetching: {link}")

        try:
            parsed = parse_policy_page(
                link,
                policy_name=policy_name,  # fallback 해시가 필요할 때만 사용
                max_retries=args.max_retries,
                min_sleep=args.min_sleep,
                max_sleep=args.max_sleep
            )

            # ✅ parser가 만든 policy_id/source/canonical을 그대로 저장 (여기서 덮어쓰지 않음)
            record = {
                "policy_id": parsed.policy_id,
                "policy_name": policy_name,
                "target_group": target_group,
                "summary": summary,
                "link": parsed.canonical_link,

                "eligibility": parsed.eligibility,
                "benefit": parsed.benefit,
                "apply_process": parsed.apply_process,
                "apply_period": parsed.apply_period,

                "raw_text": parsed.raw_text,
                "source": parsed.source,
            }

            upsert_raw_policy(conn, record)
            print(f"  -> Saved: policy_id={parsed.policy_id}, source={parsed.source}")

        except Exception as e:
            print(f"  !! Failed: {e}")

        time.sleep(random.uniform(args.min_sleep, args.max_sleep))

    conn.close()
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
