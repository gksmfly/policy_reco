import streamlit as st

def profile_form():
    with st.form("profile_form"):
        age = st.number_input("나이", min_value=18, max_value=60, value=25)
        income = st.number_input("월 소득 (만원)", min_value=0, value=250)
        assets = st.number_input("총 자산 (만원)", min_value=0, value=1000)
        houseless = st.checkbox("무주택 여부", value=True)

        submitted = st.form_submit_button("추천 받기")

        if submitted:
            return {
                "age": age,
                "income": income,
                "assets": assets,
                "houseless": houseless
            }
    return None