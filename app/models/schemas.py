from typing import Literal, Optional, Any, Dict, List
from pydantic import BaseModel, Field

FieldChoice = Literal["first", "last", "full"]

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    field: FieldChoice = "full"
    methods: List[str] = Field(default_factory=lambda: ["rapidfuzz_ratio", "rapidfuzz_token_sort", "rapidfuzz_token_set"])
    limit: int = 10
    score_cutoff: int = 70
    method_params: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # example: {"rapidfuzz_ratio": {"processor": "identity"}}

class MatchHit(BaseModel):
    index: int
    first_name: str
    last_name: str
    full_name: str
    score: float
    extras: Dict[str, Any] = Field(default_factory=dict)

class MethodResult(BaseModel):
    method: str
    hits: List[MatchHit]

class SearchResponse(BaseModel):
    query: str
    fields: List[FieldChoice]
    results: List[MethodResult]
