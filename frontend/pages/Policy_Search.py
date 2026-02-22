import streamlit as st
from clients.api_client import get_policies
from components.cards import policy_card


def render():
    st.markdown("### 🔎 정책 검색")

    # -----------------------------
    # 검색 입력
    # -----------------------------
    col1, col2 = st.columns([3, 1])

    with col1:
        keyword = st.text_input("정책명 또는 키워드 검색")

    with col2:
        search_btn = st.button("검색")

    # -----------------------------
    # 고급 필터 (현재는 UI만 존재)
    # -----------------------------
    with st.expander("고급 필터"):
        age = st.number_input("연령 (선택)", min_value=0, max_value=120, value=0)
        income = st.number_input("월소득 (선택)", min_value=0, value=0)

    # -----------------------------
    # 검색 실행
    # -----------------------------
    if search_btn or keyword:

        data = get_policies()

        # 🔥 완전 안전 파싱
        policies = []

        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], list):
                policies = data["results"]
            else:
                st.error("API 응답 형식 오류 (results 없음)")
                return

        elif isinstance(data, list):
            policies = data

        else:
            st.error("API 응답이 리스트가 아님")
            return

        # 🔥 dict 아닌 값 제거 (핵심)
        policies = [p for p in policies if isinstance(p, dict)]

        # -----------------------------
        # 키워드 필터 (프론트 필터)
        # -----------------------------
        if keyword:
            keyword_lower = keyword.lower()

            filtered = []
            for p in policies:
                name = str(p.get("policy_name", "") or "").lower()
                summary = str(p.get("summary", "") or "").lower()

                if keyword_lower in name + summary:
                    filtered.append(p)

            policies = filtered

        # -----------------------------
        # 결과 없음 처리
        # -----------------------------
        if not policies:
            st.warning("검색 결과 없음")
            return

        st.markdown(f"총 {len(policies)}건")

        # -----------------------------
        # 카드 렌더링
        # -----------------------------
        for p in policies:
            policy_card(p)