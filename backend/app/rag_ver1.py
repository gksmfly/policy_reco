import os
import pandas as pd

from openai import OpenAI

from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding


CSV_PATH = os.path.join(os.getcwd(), "../data", "policy_saving_sentences.csv")

EMBED_MODEL_NAME = "text-embedding-3-small"
GEN_MODEL_NAME = "gpt-4o"


def load_documents(csv_path: str) -> list[Document]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    df = pd.read_csv(csv_path)

    # 최소 컬럼: sentence, index
    if "sentence" not in df.columns or "index" not in df.columns:
        raise ValueError("CSV에는 최소 'sentence', 'index' 컬럼이 필요합니다.")

    docs: list[Document] = []
    for _, row in df.iterrows():
        text = str(row["sentence"])
        doc_id = int(row["index"])
        docs.append(
            Document(
                text=text,
                metadata={"doc_id": doc_id},
            )
        )
    return docs


def build_index(documents: list[Document]) -> VectorStoreIndex:
    embed_model = OpenAIEmbedding(model=EMBED_MODEL_NAME)
    return VectorStoreIndex.from_documents(documents, embed_model=embed_model)


def retrieve(index: VectorStoreIndex, query: str, top_k: int = 5):
    retriever = index.as_retriever(top_k=top_k, verbose=True)
    results = retriever.retrieve(query)

    hits = []
    for rank, r in enumerate(results, start=1):
        hits.append(
            {
                "rank": rank,
                "doc_id": r.metadata.get("doc_id"),
                "score": float(r.score) if r.score is not None else None,
                "text": r.text,
            }
        )
    return hits


def generate_answer(query: str, hits: list[dict]) -> str:
    client = OpenAI()

    # 컨텍스트 구성 (A 플랜: 정책 후보 검색이 목적이라, 텍스트 덩어리 그대로 넣음)
    context_lines = []
    for h in hits:
        # 너무 길면 비용/토큰이 커질 수 있어 간단히 컷(필요시 조절)
        snippet = h["text"][:1500]
        context_lines.append(
            f"[{h['rank']}] (doc_id={h['doc_id']}, score={h['score']})\n{snippet}"
        )

    context = "\n\n".join(context_lines)

    prompt = f"""
너는 주거/복지 정책 안내 도우미야.
아래 [검색결과]만 근거로 사용해서 답해. 근거 밖 추측은 하지 마.
가능하면 답변 끝에 참고한 doc_id를 함께 적어줘.

[검색결과]
{context}

[질문]
{query}

[답변]
""".strip()

    resp = client.responses.create(
        model=GEN_MODEL_NAME,
        input=prompt,
    )
    return resp.output_text


def main():
    print("Loading documents...")
    documents = load_documents(CSV_PATH)

    print("Building index with OpenAI embeddings...")
    index = build_index(documents)

    while True:
        query = input("\n질문을 입력하세요 (종료: 엔터만 입력): ").strip()
        if not query:
            break

        hits = retrieve(index, query, top_k=5)

        print("\n[Top-5 Retrieval 결과 요약]")
        for h in hits:
            print(f"- rank={h['rank']}, doc_id={h['doc_id']}, score={h['score']}")

        answer = generate_answer(query, hits)
        print("\n[GPT-4o 답변]")
        print(answer)


if __name__ == "__main__":
    main()
