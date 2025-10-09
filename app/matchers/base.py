from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Iterable, Dict, Any, List
import pandas as pd

class Matcher(Protocol):
    name: str
    def search(
        self,
        query: str,
        df: pd.DataFrame,
        fields: List[str],
        limit: int,
        score_cutoff: int,
        params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        ...

# Simple registry so new matchers auto-discoverable
_REGISTRY: dict[str, type] = {}

def register(name: str, scorer=None):
    def _wrap(cls):
        _REGISTRY[name] = cls
        cls.name = name
        if scorer is not None:
            cls._SCORER = staticmethod(scorer)
        return cls
    return _wrap

def get_matcher(name: str) -> Matcher:
    cls = _REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown matcher: {name}")
    return cls()

def list_matchers() -> List[str]:
    return sorted(_REGISTRY.keys())
