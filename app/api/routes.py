from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from app.models.schemas import SearchRequest, SearchResponse, MethodResult, MatchHit
from app.core.config import settings
from app.services.matcher_service import MatcherService

router = APIRouter()

def get_services(req: Request) -> MatcherService:
    svc: MatcherService = req.app.state.matcher_service
    return svc

@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, svc: MatcherService = Depends(get_services)):
    limit = min(max(payload.limit, 1), settings.max_limit)
    results = svc.run_methods(
        query=payload.query,
        field=payload.field,
        methods=payload.methods,
        limit=limit,
        score_cutoff=payload.score_cutoff,
        method_params=payload.method_params
    )
    return SearchResponse(
        query=payload.query,
        fields=[payload.field],  # still modeled as list in response
        results=[
            MethodResult(method=r["method"], hits=[MatchHit(**h) for h in r["hits"]])
            for r in results
        ]
    )
