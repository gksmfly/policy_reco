# Policy Reco — Seoul Youth Housing Policy Recommendation System

> **TL;DR**: Recommends Seoul housing support policies to young applicants based on eligibility conditions (age, income, assets, housing status), with RAG-powered conversational Q&A and TF-IDF similarity search.

---

## Problem Statement

Seoul operates dozens of youth housing support programs, each with different eligibility rules for age, income, asset limits, and housing status. Finding the right program requires reading through lengthy policy documents with overlapping criteria.

- Users can't easily determine which programs they qualify for without manually checking each policy's conditions
- Conversational follow-up ("what if my income changes?") isn't supported by static FAQ pages
- Similar policies are hard to discover, causing users to miss alternatives they'd qualify for

---

## Approach

- **Hard filter before ranking**: Eligibility conditions (age range, income ceiling, asset ceiling, housing status) are applied as mandatory filters first, eliminating clearly ineligible policies before heuristic scoring — this avoids presenting policies the user definitively cannot access
- **TF-IDF for similarity search**: Dense embedding similarity is overkill for keyword-heavy policy names and summaries; TF-IDF + cosine similarity gives fast, interpretable "find similar policies" results without GPU dependency
- **Why LlamaIndex for RAG Q&A?** Provides conversation history passthrough out of the box, enabling multi-turn follow-up questions on the same policy context without custom session management

---

## Key Results

| Feature | Detail |
|---------|--------|
| Eligibility filters | Age, income, assets, housing status (is_homeless) |
| Recommendation output | Top-K policies + per-condition met/unmet breakdown |
| Q&A | Multi-turn RAG with conversation history |
| Similarity search | TF-IDF cosine similarity on policy name + summary + clean_text |
| Data source | Scraped and cleaned Seoul housing portal CSV |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python |
| Frontend | Streamlit |
| Data | Pandas (CSV, in-memory) |
| Similarity | scikit-learn (TF-IDF, cosine similarity) |
| RAG | LlamaIndex 0.10.30 |
| LLM | OpenAI GPT-4o |

---

## Project Structure

```
policy_reco/
├── backend/app/
│   ├── core/data_manager.py      # CSV loading and in-memory data management
│   ├── routers/                  # policies, recommend, policy_qa, similar
│   ├── services/orchestration/   # qa_flow, recommend_flow, similar_flow
│   └── main.py
├── frontend/
│   ├── pages/                    # Recommend, Policy_QA, Policy_Search, Similar
│   └── Home.py
├── pipeline/cleaner/             # CSV cleaning, eligibility condition parsing
│   └── rules/                    # parse_age, parse_income, parse_assets, parse_car
└── data_collection/              # Crawler, merger, parser notebooks
```

---

## Getting Started

```bash
# 1. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Environment variables
echo "OPENAI_API_KEY=your_key_here" > .env

# 3. Start backend
uvicorn backend.app.main:app --reload
# Swagger: http://localhost:8000/docs

# 4. Start frontend
streamlit run frontend/Home.py
```

---

## Limitations & Future Work

- All data is loaded into memory at startup; replacing CSV with PostgreSQL would enable filtering at the DB layer and support larger policy datasets
- TF-IDF similarity doesn't capture semantic paraphrasing; upgrading to dense embedding search would improve similarity quality
- Future: personalized recommendation history; automated policy data refresh pipeline; eligibility pre-check before Q&A

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Seoyeon Kim** | Undergraduate Researcher  
[GitHub](https://github.com/gksmfly) · [Email](mailto:gimhaneul24@gmail.com)
