import streamlit as st
from clients.api_client import policy_qa

st.title("정책 Q&A")

question = st.text_input("질문을 입력하세요")

if st.button("질문하기"):
    if question:
        result = policy_qa({"question": question})
        st.write(result.get("answer", "답변 없음"))