import streamlit as st

def profile_form():
    """
    기존 Recommend 화면에서 쓰는 사용자 프로필 입력 폼.
    반환값은 backend /recommend에 던질 dict 형태로 맞춤.
    (필드명은 필요 시 백엔드 스키마에 맞게 조정)
    """
    st.markdown("#### 사용자 조건 입력")

    age = st.number_input("나이", min_value=0, max_value=120, value=25, step=1)

    monthly_income = st.number_input("월 소득 (만원)", min_value=0, value=250, step=10)
    total_asset = st.number_input("총 자산 (만원)", min_value=0, value=1000, step=50)

    is_homeless = st.checkbox("무주택 여부", value=True)

    if st.button("추천 받기"):
        return {
            "age": int(age),
            "income": int(monthly_income) * 10000,  # (만원 → 원) 변환이 필요 없으면 이 줄 제거
            "asset": int(total_asset) * 10000,     # (만원 → 원)
            "is_homeless": bool(is_homeless),
        }

    return None