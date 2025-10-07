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
    results = svc.run_methods(
        query=payload.query,
        field=payload.field,
        methods=payload.methods,            # None or [] -> defaults to all in service
        limit=payload.limit,                # clamped in service
        score_cutoff=payload.score_cutoff,  # defaulted in service if None
        method_params=payload.method_params # {} defaulted in service if None
    )
    return SearchResponse(
        query=payload.query,
        fields=[payload.field],
        results=[
            MethodResult(
                method=r["method"],
                duration_ms=r.get("duration_ms"),
                hits=[MatchHit(**h) for h in r["hits"]],
            )
            for r in results
        ]
    )
