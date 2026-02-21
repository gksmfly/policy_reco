from fastapi import APIRouter
from app.services.orchestration.qa_flow import run_policy_qa

router = APIRouter()

@router.post("/policy-qa")
def policy_qa(payload: dict):
    question = payload.get("question")
    return run_policy_qa(question)
