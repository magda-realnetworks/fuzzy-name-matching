"""
RapidFuzz-based matchers for the fuzzy search app.

Assumes the DataFrame passed in has:
  - a column "name"    : the original (display) string
  - a column "name_lc" : the lowercase string used for scoring

Each matcher implements a .search(...) method with signature:
    search(self, query, df, fields, limit, score_cutoff, params=None)
`fields` is kept for compatibility but will be ignored (we always use df["name_lc"]).

Returns a list of dicts (hits) with keys:
  - index (int): row index in the passed df (or position)
  - first_name (str): left empty (kept for schema compatibility)
  - last_name (str): left empty
  - full_name (str): the matched string (row["name"])
  - score (float): match score
  - extras (dict): extension point
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
import pandas as pd

from rapidfuzz import fuzz, process

from app.matchers.base import register

# ---- utilities ----

def _select_scorer(kind: str):
    """Return a RapidFuzz scorer function for the kind string."""
    if kind == "ratio":
        return fuzz.ratio
    if kind == "token_sort":
        return fuzz.token_sort_ratio
    if kind == "token_set":
        return fuzz.token_set_ratio
    raise ValueError(f"Unknown scorer kind: {kind}")


def _extract_top(
    query_lc: str,
    choices: List[str],
    scorer,
    limit: int,
    score_cutoff: int
) -> List[Tuple[str, float, int]]:
    """
    Wrapper around rapidfuzz.process.extract that returns
    a list of (match_value, score, position).
    `choices` should be an array-like (e.g., df["name_lc"].values).
    """
    # process.extract returns (match, score, index) when choices is a sequence
    return process.extract(
        query_lc,
        choices,
        scorer=scorer,
        score_cutoff=score_cutoff,
        limit=limit
    )


def _format_hits_from_rows(hits: List[Tuple[str, float, int]], df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert RapidFuzz hits (match_val, score, row_pos) to the standard output dicts.
    Use df.iloc[row_pos] to get the matched row.
    """
    out = []
    for match_val, score, row_pos in hits:
        # row_pos is an integer position into the choices sequence; map to the dataframe row
        try:
            row = df.iloc[row_pos]
        except Exception:
            # safeguard: if iloc fails, skip the hit
            continue
        out.append({
            "index": int(row_pos),
            "first_name": "",
            "last_name": "",
            "full_name": row["name"],
            "score": float(score),
            "extras": {}
        })
    return out


# ---- Matchers ----

@register("rapidfuzz_ratio")
class RapidFuzzRatio:
    """
    Uses fuzz.ratio over df["name_lc"].
    """
    def search(
        self,
        query: str,
        df: pd.DataFrame,
        fields: List[str],
        limit: int,
        score_cutoff: int,
        params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        scorer = _select_scorer("ratio")
        query_lc = query.lower()
        choices = df["name_lc"].values
        hits = _extract_top(query_lc, choices, scorer, limit, score_cutoff)
        return _format_hits_from_rows(hits, df)


@register("rapidfuzz_token_sort")
class RapidFuzzTokenSort:
    """
    Uses fuzz.token_sort_ratio over df["name_lc"].
    """
    def search(
        self,
        query: str,
        df: pd.DataFrame,
        fields: List[str],
        limit: int,
        score_cutoff: int,
        params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        scorer = _select_scorer("token_sort")
        query_lc = query.lower()
        choices = df["name_lc"].values
        hits = _extract_top(query_lc, choices, scorer, limit, score_cutoff)
        return _format_hits_from_rows(hits, df)


@register("rapidfuzz_token_set")
class RapidFuzzTokenSet:
    """
    Uses fuzz.token_set_ratio over df["name_lc"].
    """
    def search(
        self,
        query: str,
        df: pd.DataFrame,
        fields: List[str],
        limit: int,
        score_cutoff: int,
        params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        scorer = _select_scorer("token_set")
        query_lc = query.lower()
        choices = df["name_lc"].values
        hits = _extract_top(query_lc, choices, scorer, limit, score_cutoff)
        return _format_hits_from_rows(hits, df)
