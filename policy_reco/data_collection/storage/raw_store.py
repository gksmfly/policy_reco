# raw_store.py
# ------------------------------------------------------------
# 역할
# - raw_policies (최신본) upsert
# - raw_policy_versions (히스토리) append:
#   같은 policy_id라도 version_hash가 새로 생기면 새 버전으로 저장
# ------------------------------------------------------------

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    import re
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compute_version_hash(record: Dict[str, Any]) -> str:
    """
    변경 감지용 hash:
    - 의미 있는 내용 필드 위주로 구성 (메타: policy_id/link/source/fetched_at 제외)
    """
    payload = {
        "policy_name": normalize_whitespace(record.get("policy_name", "")),
        "target_group": normalize_whitespace(record.get("target_group", "")),
        "summary": normalize_whitespace(record.get("summary", "")),
        "eligibility": normalize_whitespace(record.get("eligibility", "")),
        "benefit": normalize_whitespace(record.get("benefit", "")),
        "apply_process": normalize_whitespace(record.get("apply_process", "")),
        "apply_period": normalize_whitespace(record.get("apply_period", "")),
        "raw_text": normalize_whitespace(record.get("raw_text", "")),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_policies (
            policy_id TEXT PRIMARY KEY,
            policy_name TEXT,
            target_group TEXT,
            summary TEXT,
            link TEXT,
            eligibility TEXT,
            benefit TEXT,
            apply_process TEXT,
            apply_period TEXT,
            raw_text TEXT,
            version_hash TEXT,
            fetched_at_utc TEXT,
            source TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_policy_versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id TEXT NOT NULL,
            version_hash TEXT NOT NULL,
            fetched_at_utc TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_versions_policy_id ON raw_policy_versions(policy_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_versions_policy_hash ON raw_policy_versions(policy_id, version_hash)"
    )

    conn.commit()


def upsert_raw_policy(conn: sqlite3.Connection, record: Dict[str, Any]) -> None:
    """
    1) raw_policies 최신본 upsert
    2) raw_policy_versions에 버전 히스토리 추가(중복 버전은 추가 안 함)
    """
    ensure_tables(conn)

    fetched_at_utc = datetime.now(timezone.utc).isoformat()
    version_hash = compute_version_hash(record)

    # --- 1) 최신본 테이블 upsert ---
    conn.execute(
        """
        INSERT INTO raw_policies (
            policy_id, policy_name, target_group, summary, link,
            eligibility, benefit, apply_process, apply_period,
            raw_text, version_hash, fetched_at_utc, source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(policy_id) DO UPDATE SET
            policy_name=excluded.policy_name,
            target_group=excluded.target_group,
            summary=excluded.summary,
            link=excluded.link,
            eligibility=excluded.eligibility,
            benefit=excluded.benefit,
            apply_process=excluded.apply_process,
            apply_period=excluded.apply_period,
            raw_text=excluded.raw_text,
            version_hash=excluded.version_hash,
            fetched_at_utc=excluded.fetched_at_utc,
            source=excluded.source
        """,
        (
            record.get("policy_id"),
            record.get("policy_name", ""),
            record.get("target_group", ""),
            record.get("summary", ""),
            record.get("link", ""),
            record.get("eligibility", ""),
            record.get("benefit", ""),
            record.get("apply_process", ""),
            record.get("apply_period", ""),
            record.get("raw_text", ""),
            version_hash,
            fetched_at_utc,
            record.get("source", "unknown"),
        )
    )

    # --- 2) 버전 테이블: 같은 policy_id + version_hash가 이미 있으면 skip ---
    exists = conn.execute(
        """
        SELECT 1
        FROM raw_policy_versions
        WHERE policy_id = ? AND version_hash = ?
        LIMIT 1
        """,
        (record.get("policy_id"), version_hash)
    ).fetchone()

    if not exists:
        # payload_json은 “그 시점의 스냅샷” (필요 필드만)
        payload = {
            "policy_id": record.get("policy_id"),
            "policy_name": record.get("policy_name", ""),
            "target_group": record.get("target_group", ""),
            "summary": record.get("summary", ""),
            "link": record.get("link", ""),
            "eligibility": record.get("eligibility", ""),
            "benefit": record.get("benefit", ""),
            "apply_process": record.get("apply_process", ""),
            "apply_period": record.get("apply_period", ""),
            "raw_text": record.get("raw_text", ""),
            "source": record.get("source", "unknown"),
        }
        payload_json = json.dumps(payload, ensure_ascii=False)

        conn.execute(
            """
            INSERT INTO raw_policy_versions (policy_id, version_hash, fetched_at_utc, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (record.get("policy_id"), version_hash, fetched_at_utc, payload_json)
        )

    conn.commit()
