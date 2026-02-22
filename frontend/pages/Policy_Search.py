import streamlit as st
from clients.api_client import get_policies, recommend
from components.cards import policy_card


def render():

    st.markdown("## 🔎 정책 검색")

    # ==================================================
    # 1️⃣ 기본 키워드 검색
    # ==================================================
    keyword = st.text_input("정책명 또는 키워드 검색")

    # ==================================================
    # 2️⃣ 심화 조건 (조건 기반 추천)
    # ==================================================
    with st.expander("고급 필터"):

        age = st.number_input("나이", min_value=0, max_value=120, value=0)
        monthly_income = st.number_input("월 소득 (만원)", min_value=0, value=0)
        total_asset = st.number_input("총 자산 (만원)", min_value=0, value=0)
        is_homeless = st.checkbox("무주택 여부", value=False)

    search_btn = st.button("검색")

    if not search_btn:
        return

    # ==================================================
    # 3️⃣ 조건이 하나라도 있으면 → recommend API 사용
    # ==================================================
    use_recommend = any([
        age > 0,
        monthly_income > 0,
        total_asset > 0,
        is_homeless
    ])

    if use_recommend:

        profile = {
            "age": age,
            "income": monthly_income * 10000 * 12,
            "assets": total_asset * 10000,
            "is_homeless": is_homeless
        }

        result = recommend(profile)
        policies = result.get("results", [])

        st.markdown("### 🔥 조건 기반 추천 결과")

    else:
        data = get_policies()

        if isinstance(data, dict) and "results" in data:
            policies = data["results"]
        elif isinstance(data, list):
            policies = data
        else:
            st.error("API 응답 오류")
            return

        st.markdown("### 📋 전체 정책 검색 결과")

    # ==================================================
    # 4️⃣ 키워드 필터
    # ==================================================
    if keyword:
        keyword_lower = keyword.lower()

        policies = [
            p for p in policies
            if keyword_lower in str(p.get("policy_name", "")).lower()
            or keyword_lower in str(p.get("summary", "")).lower()
        ]

    if not policies:
        st.warning("결과 없음")
        return

    st.markdown(f"총 {len(policies)}건")

    for p in policies:
        policy_card(p)