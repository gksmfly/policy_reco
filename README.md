# 🏠 Youth Housing Policy Recommendation System

서울 주거 포털 정책 데이터를 기반으로\
사용자 조건(연령, 소득, 자산, 무주택 여부 등)에 맞는\
주거 정책을 추천하는 AI 기반 시스템입니다.

------------------------------------------------------------------------

## 📌 Overview

본 프로젝트는 정책 데이터를 수집·정제·매칭하여\
사용자 맞춤형 주거 정책을 추천하고,

-   조건 기반 정책 추천
-   추천 이유 자동 생성 (GPT-4o)
-   정책 Q&A (RAG 기반)
-   유사 정책 검색 (TF-IDF 기반)

을 제공하는 End-to-End 시스템입니다.

⚠️ 현재 구현은 **DB 없이 CSV 기반(in-memory) 구조**로 동작합니다.

------------------------------------------------------------------------

## 🛠 Tech Stack

### Backend

-   FastAPI
-   Pandas (CSV 기반 데이터 로딩)
-   Scikit-learn (TF-IDF, Cosine Similarity)

### Frontend

-   Streamlit

### AI

-   OpenAI GPT-4o (설명 생성)
-   OpenAI Embedding (RAG용 벡터 검색)

### Dev Environment

-   Python 3.11+

------------------------------------------------------------------------

## 🚀 Features

### 1️⃣ 조건 기반 정책 추천 엔진

-   사용자 프로필 기반 하드 필터링
-   소프트 스코어링 기반 Top-K 추천
-   충족/미충족 조건 근거 반환
-   GPT 기반 자연어 추천 설명 생성

------------------------------------------------------------------------

### 2️⃣ 정책 Q&A (RAG 기반)

-   사용자 질문 입력
-   정책 텍스트 벡터 검색
-   검색된 컨텍스트 기반 GPT 응답 생성

#### RAG Flow

    User Question
            ↓
    Embedding
            ↓
    Top-K Context Retrieval
            ↓
    GPT-4o Answer

------------------------------------------------------------------------

### 3️⃣ 유사 정책 검색 (TF-IDF 기반)

-   정책명 + 요약 + clean_text 기반 TF-IDF 벡터화
-   Cosine Similarity 기반 Top-K 유사 정책 반환
-   policy_id 또는 policy_name 입력 허용
-   외부 벡터 DB 없이 CSV 기반 동작

------------------------------------------------------------------------

## 🏗 System Architecture

    [Data Crawling]
            ↓
    [Data Cleaning]
            ↓
    [CSV Storage]
            ↓
    [Matching & Similar Engine]
            ↓
    [FastAPI]
            ↓
    [Streamlit UI]

------------------------------------------------------------------------

## 📂 Project Structure

    backend/
    │
    ├── app/
    │   ├── main.py
    │   ├── routers/
    │   │   ├── policies.py
    │   │   ├── recommend.py
    │   │   ├── policy_qa.py
    │   │   └── similar.py
    │   │
    │   ├── services/
    │   │   └── orchestration/
    │   │       └── similar_flow.py
    │   │
    │   ├── pipeline/
    │   │   └── rag_qa_ver2.py
    │   │
    │   └── core/
    │       └── data_manager.py
    │
    frontend/
    │
    ├── Home.py
    ├── pages/
    │   ├── Recommend.py
    │   ├── Policy_List.py
    │   ├── Policy_QA.py
    │   └── Similar.py
    │
    ├── components/
    │   └── cards.py
    │
    └── clients/
        └── api_client.py

------------------------------------------------------------------------

## 📡 API Endpoints

### 🔹 GET `/health`

서버 상태 확인

### 🔹 GET `/policies`

전체 정책 목록 조회

### 🔹 GET `/policies/{policy_id}`

특정 정책 상세 조회

### 🔹 POST `/recommend`

사용자 조건 기반 정책 추천

``` json
{
  "age": 25,
  "income": 32000000,
  "asset": 150000000,
  "is_homeless": true
}
```

### 🔹 POST `/policy-qa`

정책 관련 질문 응답 (RAG 기반)

``` json
{
  "question": "청년 전세 지원 정책 신청 조건이 뭐야?"
}
```

### 🔹 GET `/similar/{policy_input}`

유사 정책 Top-K 반환\
- 숫자 입력 시 policy_id 기준\
- 문자열 입력 시 policy_name 부분 검색

------------------------------------------------------------------------

## ⚙️ Installation & Run

### 1️⃣ Clone Repository

    git clone <repository_url>
    cd youth-housing-policy

### 2️⃣ Create Virtual Environment

    python -m venv venv
    source venv/bin/activate   # macOS / Linux
    venv\Scripts\activate    # Windows

### 3️⃣ Install Dependencies

    pip install -r requirements.txt

### 4️⃣ Set Environment Variables

`.env` 파일 생성

    OPENAI_API_KEY=your_key_here

### 5️⃣ Run Backend

    uvicorn backend.app.main:app --reload

### 6️⃣ Run Frontend

    streamlit run frontend/Home.py

------------------------------------------------------------------------

## 🧠 Design Principles

-   GPT는 반드시 매칭 결과 기반으로만 설명 생성
-   Hallucination 최소화를 위한 RAG 구조 적용
-   Top-K 검색 후 score 기반 정렬
-   JSON 직렬화 안전 처리 (NaN 방지)
-   현재 구현은 DB 없이 CSV 기반 메모리 로딩 구조

------------------------------------------------------------------------

## 📄 License

This project is for academic / club project purposes only.
