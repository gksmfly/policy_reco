import streamlit as st
from clients.api_client import get_policies
from components.cards import policy_card

def render():
    st.markdown("### 🔎 정책 검색")

    # --- 검색 입력 ---
    col1, col2 = st.columns([3,1])

    with col1:
        keyword = st.text_input("정책명 또는 키워드 검색")

    with col2:
        search_btn = st.button("검색")

    # --- 필터 ---
    with st.expander("고급 필터"):
        age = st.number_input("연령 (선택)", min_value=0, max_value=120, value=0)
        income = st.number_input("월소득 (선택)", min_value=0, value=0)

    # --- 데이터 호출 ---
    if search_btn or keyword:
        data = get_policies()

        policies = data.get("results", data) if isinstance(data, dict) else data

        # 키워드 필터 (프론트 단 필터링)
        if keyword:
            policies = [
                p for p in policies
                if keyword.lower() in (p.get("policy_name","").lower()
                                       + p.get("summary","").lower())
            ]

        if not policies:
            st.warning("검색 결과 없음")
            return

        st.markdown(f"총 {len(policies)}건")

        for p in policies:
            policy_card(p)