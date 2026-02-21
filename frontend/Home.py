import streamlit as st

# Proxy page modules
from pages.Recommend import render as render_recommend
from pages.Policy_Search import render as render_policy_search
from pages.Policy_QA import render as render_policy_qa
from pages.Similar import render as render_similar


st.set_page_config(
    page_title="Youth Housing Policy Reco",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------- GLOBAL STYLE ----------------------
st.markdown("""
<style>

/* Hide Streamlit default sidebar */
section[data-testid="stSidebar"] { display: none !important; }
button[kind="header"] { display:none; }

/* Remove top blank space issue */
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.6rem !important; padding-bottom: 3rem; }

/* App background */
html, body, [data-testid="stAppViewContainer"] {
    background: #ffffff;
}

/* ================= HEADER ================= */
.boaz-header {
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding: 18px 24px;
    border-radius: 16px;
    border: 1px solid rgba(37, 99, 235, 0.15);
    background: linear-gradient(
        90deg,
        rgba(59,130,246,0.12),
        rgba(255,255,255,1)
    );
    margin-bottom: 18px;
}

.boaz-title {
    font-size: 24px;
    font-weight: 800;
    color: #1e3a8a;
}

.boaz-subtitle {
    font-size: 14px;
    color: rgba(30, 58, 138, 0.75);
    margin-top: 4px;
}

/* ================= TABS ================= */

/* Tab container */
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    justify-content: space-between !important;
    gap: 14px;
    margin-top: 10px;
    margin-bottom: 20px;
}

/* Individual tab */
.stTabs [data-baseweb="tab"] {
    flex: 1;
    text-align: center;
    border-radius: 999px;
    padding: 10px 0;
    font-weight: 500;
    background: #ffffff;
    border: 1px solid rgba(37, 99, 235, 0.18);
    transition: all 0.2s ease;
}

/* Selected tab */
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.18);
    border-color: rgba(59,130,246,0.55);
    font-weight: 600;
}

/* Hover effect */
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(59,130,246,0.08);
}

/* ================= BUTTONS ================= */
.stButton > button, 
div[data-testid="stFormSubmitButton"] > button {
    background: #2563eb;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.6rem 1rem;
    font-weight: 500;
}

.stButton > button:hover {
    background: #1d4ed8;
}

/* ================= INPUTS ================= */
div[data-baseweb="input"] input, 
textarea {
    border-radius: 10px !important;
}

/* Headings */
h1, h2, h3, h4 {
    color: #0f172a;
}

</style>
""", unsafe_allow_html=True)


# ---------------------- HEADER ----------------------
st.markdown("""
<div class="boaz-header">
  <div>
    <div class="boaz-title">🏠 Youth Housing Policy Recommendation</div>
    <div class="boaz-subtitle">
        조건 기반 추천 · 유사 정책 검색 · 정책 Q&A (RAG)
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ---------------------- NAVIGATION ----------------------
tabs = st.tabs([
    "Recommend",
    "Policy List",
    "Policy Q&A",
    "Similar"
])


# ---------------------- TAB CONTENT ----------------------

with tabs[0]:
    render_recommend()


with tabs[1]:
    render_policy_search()


with tabs[2]:
    render_policy_qa()


with tabs[3]:
    render_similar()