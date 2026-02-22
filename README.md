# 🏠 Youth Housing Policy Recommendation System

서울 주거 포털 정책 데이터를 기반으로  
사용자 조건(연령, 소득, 자산, 무주택 여부 등)에 맞는  
주거 정책을 추천하는 FastAPI + Streamlit 프로젝트입니다.

> ✅ 현재 구현은 **DB 없이 CSV 기반(in-memory)** 으로 동작합니다.  
> (정책/자격조건 데이터를 `pipeline/cleaner/*.csv`에서 로딩)

---

## 🛠 Tech Stack

### Backend
- FastAPI
- Pandas (CSV 로딩)
- Scikit-learn (TF-IDF, Cosine Similarity)

### Frontend
- Streamlit

### AI
- OpenAI GPT-4o (정책 Q&A, 추천 설명)
- LlamaIndex (RAG 구성)

---

## 🚀 주요 기능

### 1) 조건 기반 정책 추천
- 사용자 프로필 기반 하드 필터 + 점수화(휴리스틱)
- Top-K 추천 결과 + 충족/미충족 근거 리스트 반환

### 2) 정책 Q&A (RAG)
- 정책 텍스트(주로 `clean_text`) 기반 검색 → LLM 답변 생성
- 대화 히스토리(history)를 함께 전달해 “이어 묻기” 지원

### 3) 유사 정책 검색 (TF-IDF 데모)
- `policy_name + support_summary + clean_text`로 TF-IDF 벡터화
- cosine similarity로 Top-K 유사 정책 반환
- **policy_id 또는 policy_name(부분일치)** 입력 지원
- FastAPI JSON 직렬화 이슈(NaN) 방어 처리 포함

---

## 📂 Project Structure (현재 리포 구조 기준)

```
policy_reco/
├─ backend/
│  └─ app/
│     ├─ main.py
│     ├─ core/
│     │  └─ data_manager.py
│     ├─ routers/
│     │  ├─ policies.py
│     │  ├─ recommend.py
│     │  ├─ policy_qa.py
│     │  └─ similar.py
│     ├─ services/
│     │  └─ orchestration/
│     │     ├─ recommend_flow.py
│     │     ├─ qa_flow.py
│     │     └─ similar_flow.py
│     ├─ pipeline/
│     │  ├─ rag_filter_ver3.py
│     │  └─ rag_qa_ver2.py
│     └─ schemas/
│        ├─ common.py
│        ├─ recommend.py
│        └─ qa.py
│
├─ frontend/
│  ├─ Home.py
│  ├─ clients/
│  │  └─ api_client.py
│  ├─ components/
│  │  ├─ cards.py
│  │  ├─ forms.py
│  │  └─ layout.py
│  └─ pages/
│     ├─ Recommend.py
│     ├─ Policy_Search.py
│     ├─ Policy_QA.py
│     └─ Similar.py
│
├─ pipeline/
│  └─ cleaner/
│     ├─ policies.csv
│     ├─ policy_eligibility.csv
│     └─ rules/...
│
├─ data_collection/        # 크롤러/수집 관련(별도 오너 영역)
└─ scripts/
```

---

## 📡 API Endpoints

### GET `/health`
서버 상태 확인

### GET `/policies`
전체 정책 목록 조회

### GET `/policies/{policy_id}`
정책 상세 조회

### POST `/recommend`
조건 기반 정책 추천

**Request 예시**
```json
{
  "age": 25,
  "income": 32000000,
  "asset": 150000000,
  "is_homeless": true
}
```

### POST `/policy-qa`
정책 Q&A (RAG)

**Request 예시**
```json
{
  "question": "청년 전세 지원 정책 신청 조건이 뭐야?",
  "history": [
    {"role": "user", "content": "청년 월세 지원 알려줘"},
    {"role": "assistant", "content": "요약 답변..."}
  ]
}
```

### GET `/similar?policy_input=...`
유사 정책 Top-K 반환 (TF-IDF 데모)

**예시**
- ID 기준: `/similar?policy_input=12`
- 정책명 기준: `/similar?policy_input=전세보증금 반환보증`

---

## ⚙️ 실행 방법

### 1) 가상환경 & 설치
```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### 2) 환경변수 설정
프로젝트 루트에 `.env` 생성:
```bash
OPENAI_API_KEY=your_key_here
```

### 3) Backend 실행
```bash
uvicorn backend.app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

### 4) Frontend 실행
```bash
streamlit run frontend/Home.py
```

---

## ✅ 메모
- 현재 단계에서는 **DB/pgvector 없이 CSV 기반**으로 기능 검증이 가능하도록 구성되어 있습니다.
- 데이터 품질(상세 설명 텍스트 정제)은 `pipeline/cleaner` 단계 품질에 따라 달라질 수 있습니다.
