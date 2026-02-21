from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# 1) .env를 '프로젝트 루트'에서 확실히 로드
ROOT_DIR = Path(__file__).resolve().parents[2]  # backend/app/db/session.py 기준 -> policy_reco/
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./policy.sqlite3")

# 2) sqlite 파일 경로면 부모 폴더 자동 생성(./data 같은 케이스)
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_file = (ROOT_DIR / db_path).resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)

def _make_engine():
    if DATABASE_URL.startswith("sqlite"):
        return create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    return create_engine(DATABASE_URL, future=True)

engine = _make_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()