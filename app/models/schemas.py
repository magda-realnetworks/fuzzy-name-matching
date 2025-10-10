from typing import Literal, Optional, Any, Dict, List
from pydantic import BaseModel, Field

FieldChoice = Literal["first", "last", "full"]

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    field: FieldChoice = "full"
    methods: List[str] = Field(...)
    formats: List[str] = Field(...)
    limit: int = 10
    score_cutoff: int = 70
    method_params: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # example: {"rapidfuzz_ratio": {"processor": "identity"}}

class MatchHit(BaseModel):
    index: int
    match: str
    score: float
    extras: Dict[str, Any] = Field(default_factory=dict)

class MethodResult(BaseModel):
    method: str
    duration_ms: float | None = None
    hits: List[MatchHit]

class FormatResult(BaseModel):
    format: str
    methods: List[MethodResult]

class SearchResponse(BaseModel):
    query: str
    fields: List[FieldChoice]
    results: List[FormatResult]
