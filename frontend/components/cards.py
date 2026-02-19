import streamlit as st

def policy_card(policy):
    with st.container():
        st.subheader(policy.get("policy_name", "정책명 없음"))
        st.write(policy.get("summary", "요약 없음"))
        if "score" in policy:
            st.write(f"적합도 점수: {policy['score']}")
        st.divider()