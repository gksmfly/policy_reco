import streamlit as st
from clients.api_client import policy_qa

def render():
    st.markdown("### 💬 정책 Q&A")

    question = st.text_area("궁금한 정책을 입력하세요", height=100)

    if st.button("질문하기"):
        if not question.strip():
            st.warning("질문을 입력하세요.")
            return

        with st.spinner("답변 생성 중..."):
            result = policy_qa({"question": question})

        answer = result.get("answer", "답변 없음")

        st.markdown("#### 🧠 답변")
        st.info(answer)

        if "sources" in result:
            st.markdown("#### 📚 참고 정책")
            for s in result["sources"]:
                st.write("-", s)