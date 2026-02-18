from fastapi import FastAPI
from .routers import health

app = FastAPI(title="Policy Recommendation API")

app.include_router(health.router)