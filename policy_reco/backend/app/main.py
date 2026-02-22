from fastapi import FastAPI
from dotenv import load_dotenv

# 🔥 .env 먼저 로드 (OpenAI 키 등)
load_dotenv()

from .routers import policies
from .routers import recommend
from .routers import policy_qa
from .routers import similar

# 🔥 RAG 엔진 preload용
from backend.app.pipeline.rag_qa_ver2 import load_rag_engine


app = FastAPI(
    title="Policy Recommendation API",
    version="1.0.0",
)

app.include_router(policies.router)
app.include_router(recommend.router)
app.include_router(policy_qa.router)
app.include_router(similar.router)


# 🔥 서버 시작 시 RAG 엔진 미리 생성
@app.on_event("startup")
def startup_event():
    print("🔄 RAG 엔진 초기화 중...")
    try:
        load_rag_engine()
        print("✅ RAG 엔진 초기화 완료")
    except Exception as e:
        print(f"❌ RAG 엔진 초기화 실패: {e}")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    return {
        "message": "Policy Recommendation API is running",
        "version": "1.0.0"
    }