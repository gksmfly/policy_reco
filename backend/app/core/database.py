from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os

# 기본값을 SQLite로 변경
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/policy.sqlite3"
)

# SQLite일 경우 멀티스레드 대응 옵션 필요 (FastAPI용)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,   # 로컬 개발용 (간단하고 안전)
        future=True,
    )
else:
    engine = create_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
