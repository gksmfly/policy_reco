from __future__ import annotations

from functools import lru_cache
from typing import List
import os

from dotenv import load_dotenv
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from backend.app.core.data_manager import get_dataframes

# .env 로드
load_dotenv()

# -----------------------------
# RAG 엔진 로드 (서버 시작 시 1회)
# -----------------------------
@lru_cache(maxsize=1)
def load_rag_engine():
    """
    - policies.csv 로드
    - clean_text 기반 문서 생성
    - OpenAI 임베딩 + GPT-4o LLM 사용
    """

    # 🔥 API 키 확인 (디버깅용)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    policies_df, _ = get_dataframes()

    documents: List[Document] = []

    for _, row in policies_df.iterrows():
        text = row.get("clean_text")

        if not isinstance(text, str):
            continue

        text = text.strip()
        if not text:
            continue

        documents.append(Document(text=text))

    if not documents:
        raise RuntimeError("RAG용 문서가 비어 있습니다.")

    # -----------------------------
    # 명시적으로 OpenAI 설정
    # -----------------------------
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.llm = OpenAI(model="gpt-4o")
    
    index = VectorStoreIndex.from_documents(documents)
    
    chat_engine = index.as_chat_engine(
        llm=OpenAI(model="gpt-4o"),
        chat_mode="context",
        verbose=True
    )
    
    return chat_engine

# -----------------------------
# 질문 처리
# -----------------------------
def ask_policy_question(question: str) -> str:
    if not question or not question.strip():
        return "질문을 입력해주세요."

    engine = load_rag_engine()
    response = engine.query(question)

    return str(response)