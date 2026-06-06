from fastapi import FastAPI
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from model_loader import load_models, get_models
from routers import score
from schemas.score import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    yield


app = FastAPI(
    title="Credit Risk Scoring API",
    description="Real-time PD / LGD / EAD scoring — Lending Club credit risk model",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(score.router, tags=["Scoring"])


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    models = get_models()
    return HealthResponse(
        status="ok" if models["loaded"] else "degraded",
        models_loaded=models["loaded"],
        version="1.0.0",
    )


@app.get("/", tags=["Health"])
def root():
    return {"message": "Credit Risk Scoring API", "docs": "/docs"}
