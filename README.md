# Youth Housing Policy Recommendation System

본 프로젝트는 서울 주거 포털 정책 데이터를 기반으로,
사용자 조건(연령, 소득, 자산, 무주택 여부 등)에 맞는
주거 정책을 추천하는 시스템입니다.

## Tech Stack
- FastAPI
- Streamlit
- PostgreSQL + pgvector
- GPT-4o (설명 생성)
- Docker

## Features
- 조건 기반 정책 추천 엔진
- 정책 유사도 검색 (Vector Search)
- 정책 Q&A (RAG 기반)
- 추천 이유 자동 생성

## Architecture
- Data Crawling → Cleaning → Matching → API → UI