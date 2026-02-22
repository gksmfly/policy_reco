import streamlit as st


def profile_form():
    """
    기존 Recommend 화면에서 쓰는 사용자 프로필 입력 폼.
    반환값은 backend /recommend에 던질 dict 형태로 맞춤.
    """
    st.markdown("#### 사용자 조건 입력")

    age = st.number_input("나이", min_value=0, max_value=120, value=25, step=1)

    # UI는 '월 소득(만원)' 입력이지만, 백엔드 필터는 '연 소득(원)' 기준으로 비교함.
    monthly_income = st.number_input("월 소득 (만원)", min_value=0, value=250, step=10)
    total_asset = st.number_input("총 자산 (만원)", min_value=0, value=1000, step=50)

    is_homeless = st.checkbox("무주택 여부", value=True)

    if st.button("추천 받기"):
        annual_income_won = int(monthly_income) * 10000 * 12  # (만원/월) → (원/년)
        total_asset_won = int(total_asset) * 10000            # (만원) → (원)

        return {
            "age": int(age),
            # ⚠️ 백엔드에서는 profile['income']을 annual_income(연소득)으로 사용함
            "income": annual_income_won,
            "assets": total_asset_won,
            "is_homeless": bool(is_homeless),
        }

    return None