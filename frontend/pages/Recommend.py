import streamlit as st
from components.forms import profile_form
from components.cards import policy_card
from clients.api_client import recommend

def render():
    st.markdown("### 정책 추천")

    profile = profile_form()

    if profile:
        result = recommend(profile)
        policies = result.get("results", [])

        if not policies:
            st.warning("추천 결과 없음")
        else:
            for p in policies:
                policy_card(p)

if __name__ == "__main__":
    render()