from fastapi import APIRouter
from ..schemas.qa import QARequest
from ..schemas.common import ok
from ..services.orchestration.qa_flow import qa_flow

router = APIRouter(prefix="/policy-qa", tags=["qa"])

@router.post("")
def policy_qa(req: QARequest):
    result = qa_flow(req.question)
    return ok(result)
