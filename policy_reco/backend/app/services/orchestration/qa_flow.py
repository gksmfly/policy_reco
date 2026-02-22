from backend.app.pipeline.rag_qa_ver2 import load_rag_engine


def run_policy_qa(question: str, history=None):
    """
    대화형 RAG 실행 함수
    - chat_engine 기반
    - multi-turn 대화 지원
    """

    if not question or not question.strip():
        return "질문을 입력해주세요."

    engine = load_rag_engine()

    # 🔹 시스템 지침 (고정 역할 정의)
    system_instruction = """
너는 한국의 청년·주거·복지 정책을 쉽게 설명해주는 상담 AI이다.
어려운 행정 용어는 최대한 쉽게 풀어서 설명하라.
친절하고 상담하듯이 말하되, 과장하거나 추측하지 마라.
제공된 정책 데이터 범위 안에서만 답변하라.

답변 규칙:
- 정책명이 있다면 먼저 명확히 제시하라.
- 지원 내용은 bullet(-) 형식으로 정리하라.
- 연령, 소득, 무주택 여부 등 핵심 조건을 쉽게 설명하라.
- 조건이 애매하면 추가 정보를 요청하라.
- 모르는 내용은 지어내지 말고 "제공된 정보에서 확인되지 않습니다."라고 말하라.
"""

    try:
        # 🔥 chat_engine 사용 (query 아님)
        response = engine.chat(
            f"{system_instruction}\n\n사용자 질문:\n{question}"
        )

        return str(response)

    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {str(e)}"