"""
DukaanPulse FastAPI Application
Single-server local MVP powering grounded local-business research-to-action.
"""
import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

from fastapi import FastAPI, HTTPException, status, APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from services.models import (
    ResearchRequest, ResearchResponse, ExperimentCreate,
    ExperimentRecord, OutcomeInput, OutcomeRecord, HealthResponse,
    MerchantEconomicsInput, EconomicsResult
)
from services.storage import Storage
from services.you_search import (
    YouSearchAdapter, SearchError, SearchConfigError, SearchAuthError,
    SearchRateLimitError, SearchNetworkError, SearchSchemaError
)
from services.synthesis import (
    SynthesisAdapter, SynthesisError, SynthesisConfigError
)
from services.validators import GroundedValidationError
from services.economics import (
    calculate_economics, check_stale_advice, EconomicsValidationError
)

app = FastAPI(
    title="DukaanPulse API",
    description="Local business research-to-action agent powered by You.com and grounded synthesis",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Restore original requested path from Vercel's rewrite headers
@app.middleware("http")
async def vercel_path_middleware(request: Request, call_next):
    forwarded_uri = (
        request.headers.get("x-forwarded-uri") or
        request.headers.get("x-matched-path") or
        request.headers.get("x-vercel-matched-path") or
        request.headers.get("x-original-uri")
    )
    if forwarded_uri and forwarded_uri != "/api/index.py":
        path_only = forwarded_uri.split("?")[0]
        request.scope["path"] = path_only

    return await call_next(request)

# Initialize storage and services
is_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
DB_PATH = os.getenv(
    "DATABASE_PATH",
    "/tmp/dukaanpulse.db" if is_serverless else "dukaanpulse.db"
)
storage = Storage(db_path=DB_PATH)


def get_search_adapter() -> YouSearchAdapter:
    api_key = os.getenv("YOU_API_KEY", "")
    search_url = os.getenv("YOU_SEARCH_URL", "https://ydc-index.io/v1/search")
    mock_mode = api_key in ("mock", "demo", "")
    return YouSearchAdapter(api_key=api_key, search_url=search_url, mock_mode=mock_mode)


def get_synthesis_adapter() -> SynthesisAdapter:
    provider = os.getenv("LLM_PROVIDER", "mock")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    mock_mode = provider == "mock" or api_key in ("mock", "demo")
    return SynthesisAdapter(provider=provider, api_key=api_key, model=model, mock_mode=mock_mode)


@app.get("/api/health", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint revealing provider configuration status without leaking secrets."""
    you_key = os.getenv("YOU_API_KEY", "")
    llm_key = os.getenv("LLM_API_KEY", "")
    llm_provider = os.getenv("LLM_PROVIDER", "mock")

    db_ok = True
    try:
        storage.list_experiments()
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok",
        you_search_configured=bool(you_key and you_key != "mock"),
        llm_configured=bool(llm_key and llm_key != "mock") or llm_provider == "mock",
        llm_provider=llm_provider,
        database_ok=db_ok
    )


@app.post("/api/economics/calculate", response_model=EconomicsResult)
@app.post("/economics/calculate", response_model=EconomicsResult)
async def evaluate_economics(inputs: MerchantEconomicsInput):
    """
    Pure deterministic managerial unit economics calculation in Python.
    Calculates variable costs, contribution margin, break-even orders, and budget checks.
    """
    try:
        return calculate_economics(inputs)
    except EconomicsValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


class StaleCheckRequest(BaseModel):
    experiment_id: str
    current_economics: MerchantEconomicsInput


class StaleCheckResponse(BaseModel):
    is_stale: bool
    stale_reason: Optional[str] = None
    economics: EconomicsResult


@app.post("/api/economics/check-stale", response_model=StaleCheckResponse)
@app.post("/economics/check-stale", response_model=StaleCheckResponse)
async def check_experiment_staleness(payload: StaleCheckRequest):
    """
    Checks whether newly entered cost assumptions invalidate a previously generated experiment.
    Prevents stale positive recommendations from remaining active.
    """
    exp = storage.get_experiment(payload.experiment_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{payload.experiment_id}' not found."
        )

    is_stale, reason = check_stale_advice(payload.current_economics, exp.assumptions_snapshot)
    recalculated = calculate_economics(payload.current_economics)

    return StaleCheckResponse(
        is_stale=is_stale,
        stale_reason=reason,
        economics=recalculated
    )


@app.post("/api/research", response_model=ResearchResponse)
@app.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    """
    Validates merchant request, executes You.com live retrieval,
    synthesizes grounded findings and bounded experiment, and persists run.
    """
    search_adapter = get_search_adapter()
    synthesis_adapter = get_synthesis_adapter()

    # 1. Retrieval stage
    try:
        evidence = await search_adapter.search(request)
    except SearchAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except SearchRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except (SearchConfigError, SearchNetworkError, SearchSchemaError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except SearchError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # 2. Grounded Synthesis stage
    try:
        report = await synthesis_adapter.synthesize(request, evidence)
    except SynthesisConfigError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except GroundedValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"AI model synthesis failed grounding check after repair attempt: {str(e)}"
        )
    except SynthesisError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # 3. Persistence stage
    research_id = storage.save_research(request, report, evidence)
    saved = storage.get_research(research_id)
    if not saved:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist research run.")

    return saved


@app.get("/api/research/{research_id}", response_model=ResearchResponse)
@app.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(research_id: str):
    """Retrieves server-stored research run with verified evidence ledger."""
    saved = storage.get_research(research_id)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{research_id}' not found."
        )
    return saved


@app.post("/api/experiments", response_model=ExperimentRecord)
@app.post("/experiments", response_model=ExperimentRecord)
async def create_experiment(input_data: ExperimentCreate):
    """
    Owner acceptance: Converts a verified, server-stored research run
    into an active experiment. Rejects client-supplied experiment fields.
    """
    exp = storage.create_experiment(input_data.research_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create experiment: research run not found or does not contain a ready experiment."
        )
    return exp


@app.get("/api/experiments")
@app.get("/experiments")
async def list_experiments():
    """Lists all local experiments with aggregated financial metrics."""
    return storage.list_experiments()


@app.get("/api/experiments/{experiment_id}", response_model=ExperimentRecord)
@app.get("/experiments/{experiment_id}", response_model=ExperimentRecord)
async def get_experiment(experiment_id: str):
    """Retrieves a single experiment with full outcome measurement ledger."""
    exp = storage.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found."
        )
    return exp


@app.post("/api/experiments/{experiment_id}/outcome", response_model=ExperimentRecord)
@app.post("/experiments/{experiment_id}/outcome", response_model=ExperimentRecord)
async def add_outcome(experiment_id: str, outcome: OutcomeInput):
    """
    Records daily experimental measurement.
    Strictly calculates contribution = revenue - variable_cost.
    """
    added = storage.add_outcome(experiment_id, outcome)
    if not added:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment '{experiment_id}' not found."
        )
    updated_exp = storage.get_experiment(experiment_id)
    return updated_exp


# Serve index.html for root route
@app.get("/")
async def serve_index():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "DukaanPulse API running. index.html not yet installed."})


# Diagnostic fallback: reports the exact URL path received by FastAPI
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path_name: str):
    return JSONResponse({
        "status": "unmatched_route",
        "received_path": request.url.path,
        "path_name": path_name,
        "headers": dict(request.headers),
        "routes": [f"{r.path} ({type(r).__name__})" for r in app.routes if hasattr(r, "path")]
    })
