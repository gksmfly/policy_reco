import streamlit as st

def policy_card(policy: dict):
    """A simple white card with blue accent."""
    title = policy.get("policy_name") or policy.get("title") or "정책명 없음"
    summary = policy.get("summary") or policy.get("support_summary") or "요약 없음"
    score = policy.get("score")

    st.markdown(
        """
<style>
.boaz-card {
  border: 1px solid rgba(30, 64, 175, 0.18);
  border-left: 6px solid rgba(37, 99, 235, 0.85);
  border-radius: 14px;
  padding: 14px 16px;
  margin: 10px 0 14px 0;
  background: #ffffff;
  box-shadow: 0 1px 8px rgba(2, 6, 23, 0.04);
}
.boaz-card h4 { margin: 0 0 6px 0; color: #1e3a8a; }
.boaz-card p { margin: 0; color: rgba(15, 23, 42, 0.85); }
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

    st.markdown('<div class="boaz-card">', unsafe_allow_html=True)
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    st.markdown(f"<p>{summary}</p>", unsafe_allow_html=True)
    if score is not None:
        st.markdown(f'<div class="boaz-badge">적합도 점수: {score}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)