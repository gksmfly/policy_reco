# 🏠 Youth Housing Policy Recommendation System

서울 주거 포털 정책 데이터를 기반으로
사용자 조건(연령, 소득, 자산, 무주택 여부 등)에 맞는
주거 정책을 추천하는 AI 기반 시스템입니다.

------------------------------------------------------------------------

## 📌 Overview

본 프로젝트는 정책 데이터를 수집·정제·매칭하여\
사용자 맞춤형 주거 정책을 추천하고,

-   추천 이유 자동 생성 (GPT-4o)
-   정책 Q&A (RAG 기반)
-   유사 정책 벡터 검색

을 제공하는 End-to-End 파이프라인 시스템입니다.

------------------------------------------------------------------------

## 🛠 Tech Stack

### Backend

-   FastAPI
-   SQLAlchemy
-   SQLite

### Frontend

-   Streamlit

### AI

-   OpenAI GPT-4o (설명 생성)
-   OpenAI Embedding (Vector Search / RAG)

### Dev Environment

-   Python 3.11+

------------------------------------------------------------------------

## 🚀 Features

### 1️⃣ 조건 기반 정책 추천 엔진

-   사용자 프로필 기반 하드 필터링
-   소프트 스코어링 기반 Top-K 정책 추천
-   충족/미충족 조건 근거 생성

------------------------------------------------------------------------

### 2️⃣ 추천 이유 자동 생성 (GPT-4o)

-   매칭 결과(충족/미충족 조건)만을 근거로 설명 생성
-   Hallucination 최소화를 위한 프롬프트 설계
-   자연어 기반 사용자 친화적 설명 제공

------------------------------------------------------------------------

### 3️⃣ 정책 유사도 검색 (Vector Search)

-   정책 설명 텍스트 임베딩
-   벡터 기반 정책 유사도 검색
-   Top-K 유사 정책 반환

------------------------------------------------------------------------

### 4️⃣ 정책 Q&A (RAG 기반)

-   사용자 질문 입력
-   정책 텍스트 벡터 검색
-   검색된 컨텍스트 기반 GPT 응답 생성

------------------------------------------------------------------------

## 🏗 System Architecture

\[Data Crawling\] ↓ \[Raw Storage\] ↓ \[Data Cleaning / Structuring\] ↓
\[Matching & Scoring Engine\] ↓ \[FastAPI\] ↓ \[Streamlit UI\]

### AI Flow (RAG)

User Question ↓ Vector Search ↓ Top-K Context Retrieval ↓ GPT-4o
Response Generation

------------------------------------------------------------------------

## 📂 Project Structure
```text
backend/ │ ├── app/ │ ├── main.py │ ├── routers/ │ │ ├── recommend.py │
│ ├── policies.py │ │ ├── policy_qa.py │ │ └── similar.py │ │ │ ├──
services/ │ ├── models/ │ └── core/ │ frontend/ │ ├── Home.py ├── pages/
│ ├── Recommend.py │ ├── Policy_Search.py │ ├── Policy_QA.py │ └──
Similar.py
```


## 📂 Project Structure

```text
backend/
│
├── app/
│   ├── main.py
│   ├── routers/
│   │   ├── recommend.py
│   │   ├── policies.py
│   │   ├── policy_qa.py
│   │   └── similar.py
│   │
│   ├── services/
│   ├── models/
│   └── core/
│
frontend/
│
├── Home.py
├── pages/
│   ├── Recommend.py
│   ├── Policy_Search.py
│   ├── Policy_QA.py
│   └── Similar.py
------------------------------------------------------------------------

## 📡 API Endpoints

### 🔹 GET `/policies`

전체 정책 목록 조회

### 🔹 GET `/policies/{id}`

특정 정책 상세 조회

### 🔹 POST `/recommend`

사용자 조건 기반 정책 추천

#### Request Example

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

### 🔹 GET `/similar/{policy_id}`

유사 정책 Top-K 반환

------------------------------------------------------------------------

## ⚙️ Installation & Run

### 1️⃣ Clone Repository

``` bash
git clone <repository_url>
cd youth-housing-policy
```

### 2️⃣ Create Virtual Environment

``` bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 3️⃣ Install Dependencies

``` bash
pip install -r requirements.txt
```

### 4️⃣ Set Environment Variables

`.env` 파일 생성

    OPENAI_API_KEY=your_key_here 
    DATABASE_URL=sqlite:///./policy.sqlite3

### 5️⃣ Run Backend

``` bash
uvicorn backend.app.main:app --reload
```

### 6️⃣ Run Frontend

``` bash
streamlit run frontend/Home.py
```

------------------------------------------------------------------------

## 🧠 AI Design Principles

-   GPT는 반드시 매칭 결과 기반으로만 설명 생성
-   외부 정보 생성 최소화 (Hallucination 방지)
-   RAG 기반 검색 후 컨텍스트 전달
-   Top-K 검색 후 score 기반 정렬

------------------------------------------------------------------------

## 🗄 Database

-   SQLite 기반 로컬 개발 환경
-   정책 원문(raw) 저장
-   정제(clean) 텍스트 저장
-   추천 실행 로그 저장

------------------------------------------------------------------------

## 👥 Role Distribution

### 1️⃣ Crawling Owner

-   정책 목록/상세 크롤링
-   Raw 데이터 저장
-   수집 이력 관리

### 2️⃣ Cleaning / Structuring Owner

-   정책 공통 스키마 설계
-   조건 파싱 및 정규화
-   Clean 데이터 적재

### 3️⃣ Matching / Scoring Engine Owner

-   하드필터 + 소프트 스코어링 설계
-   Top-K 추천 로직 구현
-   임베딩 생성 및 벡터 검색 설계

### 4️⃣ Backend / Frontend / AI Owner

-   FastAPI API 설계 및 구현
-   Streamlit UI 구현
-   GPT-4o 설명 생성
-   RAG 실행 흐름 구성
-   유사 정책 API 연결
-   SQLite 설정

------------------------------------------------------------------------

## 📌 Future Improvements

-   PostgreSQL + pgvector 마이그레이션
-   Docker Compose 기반 배포 환경 구축
-   추천 결과 캐싱 전략 도입
-   정책 자동 업데이트 파이프라인 구축

------------------------------------------------------------------------

## 📄 License

This project is for academic / club project purposes.
