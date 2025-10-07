from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import anyio
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

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
        "limit": 5,
        "results": None
    })


@app.post("/", response_class=HTMLResponse)
async def search_form(
    request: Request,
    query: str = Form(...),
    field: str = Form(...),
    methods: Optional[List[str]] = Form(None),
    limit: int = Form(5)
):
    """
    Handle form POST from templates/index.html.

    - If no methods selected, default to all registered matchers.
    - Offload the synchronous matcher work to a thread so the async loop isn't blocked.
    """
    if not methods:
        methods = list_matchers()

    svc: MatcherService = request.app.state.matcher_service

    # Offload to a worker thread to avoid blocking the event loop.
    # This assumes svc.run_methods is synchronous (as in the blueprint).
    results = await anyio.to_thread.run_sync(
        svc.run_methods,
        query,        # query
        field,        # field: "first"|"last"|"full"
        methods,      # methods list
        limit,        # limit
        None,           # score_cutoff (hard-coded default here; make configurable if you want)
        {}            # method_params
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