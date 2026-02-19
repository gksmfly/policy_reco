import streamlit as st
from clients.api_client import get_policies
from components.cards import policy_card

st.title("정책 목록")

data = get_policies()
policies = data.get("results", [])

for p in policies:
    policy_card(p)