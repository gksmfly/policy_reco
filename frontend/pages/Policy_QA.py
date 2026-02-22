# Policy_QA.py
import streamlit as st
from clients.api_client import policy_qa


def render():
    st.markdown("### 💬 정책 챗봇")

    # 🔹 세션 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 🔹 입력창 아래 공간 확보 (고정 느낌)
    st.markdown("""
        <style>
        .block-container {
            padding-bottom: 120px;
        }
        </style>
    """, unsafe_allow_html=True)

    # 🔹 대화 영역 컨테이너
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 🔹 하단 입력창
    prompt = st.chat_input("궁금한 정책을 입력하세요")

    if prompt:
        # 1️⃣ 사용자 메시지 저장
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # 2️⃣ 백엔드 호출
        response = policy_qa({
            "question": prompt,
            "history": st.session_state.messages
        })

        answer = response.get("answer", "답변 생성 실패")

        # 3️⃣ 봇 메시지 저장
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        # 🔄 새로고침으로 UI 정리
        st.rerun()