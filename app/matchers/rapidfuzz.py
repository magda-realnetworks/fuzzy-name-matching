"""
RapidFuzz-based matchers for the fuzzy search app.

Assumes the DataFrame passed in has:
  - a column "name"    : the original (display) string
  - a column "name_lc" : the lowercase string used for scoring

Each matcher implements .search(query, df, fields, limit, score_cutoff, params=None)
`fields` is ignored (we always use df["name_lc"]).

Returns a list of dicts with keys:
  - index (int): row position in df
  - first_name, last_name: left empty (schema compatibility)
  - full_name (str): matched string (row["name"])
  - score (float): match score
  - extras (dict): extension point
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
import pandas as pd

from rapidfuzz import distance, fuzz, process
from app.matchers.base import register


def _format_hits_from_rows(
    hits: List[Tuple[str, float, int]],
    df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """Convert RapidFuzz (match, score, row_pos) tuples into our hit dicts."""
    out: List[Dict[str, Any]] = []
    for _match_val, score, row_pos in hits:
        try:
            row = df.iloc[row_pos]
        except Exception:
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


def _register_matcher(name: str, scorer) -> None:
    """
    Create and register a tiny class bound to a specific RapidFuzz scorer.
    """
    @register(name)
    class _RFMatcher:
        _SCORER = staticmethod(scorer)

        def search(
            self,
            query: str,
            df: pd.DataFrame,
            fields: List[str],
            limit: int,
            score_cutoff: int,
            params: Dict[str, Any] | None = None
        ) -> List[Dict[str, Any]]:
            q = query.lower()
            choices = df["name_lc"].values
            hits = process.extract(
                q,
                choices,
                scorer=self._SCORER,
                score_cutoff=score_cutoff,
                limit=limit,
                scorer_kwargs=params
            )
            return _format_hits_from_rows(hits, df)



# ---- Register built-in RapidFuzz.fuzz scorers ----
_register_matcher("rapidfuzz_ratio", fuzz.ratio)
_register_matcher("rapidfuzz_partial_ratio", fuzz.partial_ratio)
_register_matcher("rapidfuzz_token_set_ratio", fuzz.token_set_ratio)
_register_matcher("rapidfuzz_partial_token_set_ratio", fuzz.partial_token_set_ratio)
_register_matcher("rapidfuzz_token_sort_ratio", fuzz.token_sort_ratio)
_register_matcher("rapidfuzz_partial_token_sort_ratio", fuzz.partial_token_sort_ratio)
_register_matcher("rapidfuzz_token_ratio", fuzz.token_ratio)
_register_matcher("rapidfuzz_partial_token_ratio", fuzz.partial_token_ratio)
_register_matcher("rapidfuzz_Wratio", fuzz.WRatio)
_register_matcher("rapidfuzz_Qratio", fuzz.QRatio)
#------------ methods from RapidFuzz.distance ------------
_register_matcher("rapidfuzz_DamerauLevenshtein", distance.DamerauLevenshtein.normalized_similarity)
_register_matcher("rapidfuzz_Indel", distance.Indel.normalized_similarity)
_register_matcher("rapidfuzz_Jaro", distance.Jaro.normalized_similarity)
_register_matcher("rapidfuzz_JaroWinkler", distance.JaroWinkler.normalized_similarity)
_register_matcher("rapidfuzz_Levenshtein", distance.Levenshtein.normalized_similarity)
_register_matcher("rapidfuzz_LCSseq", distance.LCSseq.normalized_similarity)
_register_matcher("rapidfuzz_OSA", distance.OSA.normalized_similarity)
_register_matcher("rapidfuzz_Prefix", distance.Prefix.normalized_similarity)
_register_matcher("rapidfuzz_Postfix", distance.Postfix.normalized_similarity)
