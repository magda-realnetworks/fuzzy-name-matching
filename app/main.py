from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import anyio
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

from app.core.config import settings
from app.services.dataset import load_dataset, DataContainer
from app.services.matcher_service import MatcherService
from app.api import router as api_router
from app.matchers.base import list_matchers

# Resolve template/static directories relative to the project root (one level above app/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

# Ensure Jinja2Templates gets a real path (avoids needing to rely on working dir)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load dataset once and attach service to app.state
    container: DataContainer = load_dataset(path=settings.data_path, limit=settings.preload_limit)
    app.state.data = container
    app.state.matcher_service = MatcherService(container)
    yield
    # Shutdown: add cleanup here if needed

# Create the FastAPI app AFTER the lifespan definition
app = FastAPI(title="Fuzzy Name Match Playground", lifespan=lifespan)

# Include API router for JSON endpoints under /api
app.include_router(api_router, prefix="/api")

# Mount static files if the folder exists (optional)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------- HTML frontend routes ----------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Render the search form. No work is done here.
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "query": "",
        "field": "full",
        "methods": [],
        "all_methods": list_matchers(),
        "limit": settings.default_limit,
        "results": None
    })


@app.post("/", response_class=HTMLResponse)
async def search_form(
    request: Request,
    query: str = Form(...),
    field: str = Form(...),
    methods: Optional[List[str]] = Form(None),
    limit: int = Form(settings.default_limit)
):
    """
    Handle form POST from templates/index.html.
    """
    if not methods:
        methods = list_matchers()

    svc: MatcherService = request.app.state.matcher_service

    results = await anyio.to_thread.run_sync(
        svc.run_methods,
        query,        # query
        field,        # "first" | "last" | "full"
        methods,      # may be None -> defaults inside service
        limit,        # may be any int -> clamped inside service
        None,         # score_cutoff -> default inside service
        None          # method_params -> {}
    )

    return templates.TemplateResponse("index.html", {
        "request": request,
        "query": query,
        "field": field,
        "methods": methods,
        "all_methods": list_matchers(),
        "limit": limit,
        "results": results
    })

# ---------- Evaluation page (no API exposure) ----------

@app.get("/eval", response_class=HTMLResponse)
async def eval_index(request: Request):
    test_dir = settings.data_path.parent / "test"
    datasets = [p.name for p in test_dir.glob("*.csv")] if test_dir.exists() else []
    return templates.TemplateResponse("eval.html", {
        "request": request,
        "datasets": datasets,
        "field": "full",
        "selected_dataset": datasets[0] if datasets else "",
        "results": None,
        "error": None,
        "active_tab": "eval",
    })


@app.post("/eval", response_class=HTMLResponse)
async def eval_run(
    request: Request,
    field: str = Form(...),                     # "first" | "last" | "full"
    dataset_name: str = Form(""),               # filename from data/test
    upload: UploadFile | None = File(None),     # optional CSV upload
):
    test_dir = settings.data_path.parent / "test"
    datasets = [p.name for p in test_dir.glob("*.csv")] if test_dir.exists() else []

    # Load pairs CSV (upload has priority)
    pairs_df = None
    source = ""
    try:
        if upload and upload.filename:
            pairs_df = pd.read_csv(upload.file)
            source = upload.filename
        elif dataset_name:
            pairs_df = pd.read_csv(test_dir / dataset_name)
            source = dataset_name
    except Exception as e:
        return templates.TemplateResponse("eval.html", {
            "request": request,
            "datasets": datasets,
            "field": field,
            "selected_dataset": dataset_name,
            "results": None,
            "error": f"Failed to read dataset: {e}",
            "active_tab": "eval",
        })

    if pairs_df is None or pairs_df.empty:
        return templates.TemplateResponse("eval.html", {
            "request": request,
            "datasets": datasets,
            "field": field,
            "selected_dataset": dataset_name,
            "results": None,
            "error": "Please choose a dataset or upload a CSV.",
            "active_tab": "eval",
        })

    # Run evaluation in a worker thread
    from app.services.evaluation import evaluate_pairs
    container: DataContainer = request.app.state.data
    try:
        results = await anyio.to_thread.run_sync(evaluate_pairs, container, field, pairs_df, None)
        error = None
    except Exception as e:
        results, error = None, str(e)

    return templates.TemplateResponse("eval.html", {
        "request": request,
        "datasets": datasets,
        "field": field,
        "selected_dataset": source or dataset_name,
        "results": results,
        "error": error,
        "active_tab": "eval",
    })
