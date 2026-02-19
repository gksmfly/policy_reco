import streamlit as st
from clients.api_client import similar
from components.cards import policy_card

st.title("유사 정책 조회")

policy_id = st.text_input("기준 정책 ID 입력")

if st.button("조회"):
    if policy_id:
        result = similar(policy_id)
        policies = result.get("results", [])

        for p in policies:
            policy_card(p)