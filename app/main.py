from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.services.dataset import load_dataset
from app.services.matcher_service import MatcherService
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load data once
    container = load_dataset(path=settings.data_path, limit=settings.preload_limit)
    app.state.df = container.df
    app.state.matcher_service = MatcherService(container.df)
    yield
    # Shutdown: nothing special

app = FastAPI(title="Fuzzy Name Match Playground", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
