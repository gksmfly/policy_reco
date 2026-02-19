from pydantic import BaseModel

class PolicyResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str | None

    class Config:
        from_attributes = True


class RecommendRequest(BaseModel):
    age: int
    income: int
    region: str


class QARequest(BaseModel):
    question: str