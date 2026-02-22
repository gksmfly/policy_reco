import streamlit as st

def policy_card(policy: dict):
    """White card with blue accent + expandable detail."""

    title = policy.get("policy_name") or policy.get("title") or "정책명 없음"
    summary = policy.get("summary") or policy.get("support_summary") or "요약 없음"
    detail = policy.get("detail") or policy.get("clean_text")
    score = policy.get("score") or policy.get("similarity_score")

    # CSS (한 번만 적용되도록)
    st.markdown(
        """
<style>
.boaz-card {
  border: 1px solid rgba(30, 64, 175, 0.18);
  border-left: 6px solid rgba(37, 99, 235, 0.85);
  border-radius: 14px;
  padding: 16px 18px;
  margin: 12px 0 16px 0;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(2, 6, 23, 0.04);
}
.boaz-card h4 {
  margin: 0 0 8px 0;
  color: #1e3a8a;
  font-weight: 600;
}
.boaz-summary {
  margin: 0 0 10px 0;
  color: rgba(15, 23, 42, 0.85);
  line-height: 1.5;
}
.boaz-badge {
  display:inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.25);
  color: #1e40af;
  margin-top: 8px;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    # 카드 시작
    st.markdown('<div class="boaz-card">', unsafe_allow_html=True)

    # 제목
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)

    # 요약
    st.markdown(f"<p class='boaz-summary'>{summary}</p>", unsafe_allow_html=True)

    # 점수 (유사도 or 추천 점수)
    if score is not None:
        try:
            score_percent = round(float(score) * 100, 1)
            st.markdown(
                f'<div class="boaz-badge">유사도: {score_percent}%</div>',
                unsafe_allow_html=True,
            )
        except:
            pass

    # 상세 설명 (접기/펼치기)
    if detail:
        with st.expander("📄 상세 설명 보기"):
            st.write(detail)

    # 카드 끝
    st.markdown("</div>", unsafe_allow_html=True)