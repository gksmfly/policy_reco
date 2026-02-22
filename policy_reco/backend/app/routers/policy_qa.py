from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

from backend.app.services.orchestration.qa_flow import run_policy_qa

router = APIRouter(prefix="/policy-qa", tags=["policy-qa"])


class QARequest(BaseModel):
    question: str
    history: List[Dict] = []


@router.post("")
def policy_qa(req: QARequest):
    answer = run_policy_qa(req.question, req.history)
    return {"answer": answer}