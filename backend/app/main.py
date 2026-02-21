from fastapi import FastAPI

from .routers import policies
from .routers import recommend
from .routers import policy_qa
from .routers import similar

app = FastAPI(
    title="Policy Recommendation API",
    version="1.0.0",
)

app.include_router(policies.router)
app.include_router(recommend.router)
app.include_router(policy_qa.router)
app.include_router(similar.router)


# Optional: root endpoint
@app.get("/")
def root():
    return {
        "message": "Policy Recommendation API is running",
        "version": "1.0.0"
    }