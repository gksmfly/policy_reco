import streamlit as st

st.set_page_config(page_title="청년 주거 정책 추천 시스템", layout="wide")

st.title("청년 주거 정책 추천 시스템")

st.markdown("""
왼쪽 사이드바에서 기능을 선택하세요.

- Recommend: 조건 기반 정책 추천
- Policy Search: 정책 목록 조회
- Policy QA: 정책 질의응답
- Similar: 유사 정책 조회
""")