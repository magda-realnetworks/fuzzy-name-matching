from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd
from rapidfuzz import fuzz, process
from app.matchers.base import register

def _select_scorer(kind: str):
    if kind == "ratio":
        return fuzz.ratio
    if kind == "token_sort":
        return fuzz.token_sort_ratio
    if kind == "token_set":
        return fuzz.token_set_ratio
    raise ValueError(f"Unknown scorer kind: {kind}")

def _search_single_field(
    query_lc: str,
    series: pd.Series,
    limit: int,
    score_cutoff: int,
    scorer
):
    # Uses RapidFuzz's extract to pull top-k; works efficiently in C++
    # Returns list of tuples (match, score, index)
    # We pass the original index via "score_cutoff" and "limit"
    return process.extract(
        query_lc,
        series.values,  # contiguous ndarray
        scorer=scorer,
        score_cutoff=score_cutoff,
        limit=limit
    )

def _merge_hits_per_field(field_hits_lists, df: pd.DataFrame, limit: int):
    # Flatten, keep best score per index, then take top-k
    best_by_idx = {}
    for hits in field_hits_lists:
        for match_val, score, row_pos in hits:
            idx = df.index[row_pos]
            if idx not in best_by_idx or score > best_by_idx[idx]:
                best_by_idx[idx] = score
    # Sort and slice
    top = sorted(best_by_idx.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return top

@register("rapidfuzz_ratio")
class RapidFuzzRatio:
    def search(self, query, df, fields, limit, score_cutoff, params=None):
        scorer = _select_scorer("ratio")
        query_lc = query.lower()
        field_map = {"first": "first_lc", "last": "last_lc", "full": "full_lc"}
        field_hits = []
        for f in fields:
            col = field_map[f]
            hits = _search_single_field(query_lc, df[col], limit, score_cutoff, scorer)
            field_hits.append(hits)
        top = _merge_hits_per_field(field_hits, df, limit)
        out = []
        for idx, score in top:
            row = df.loc[idx]
            out.append({
                "index": int(idx),
                "first_name": row.first_name,
                "last_name": row.last_name,
                "full_name": row.full_name,
                "score": float(score),
                "extras": {}
            })
        return out

@register("rapidfuzz_token_sort")
class RapidFuzzTokenSort(RapidFuzzRatio):
    def search(self, query, df, fields, limit, score_cutoff, params=None):
        scorer = _select_scorer("token_sort")
        query_lc = query.lower()
        field_map = {"first": "first_lc", "last": "last_lc", "full": "full_lc"}
        field_hits = []
        for f in fields:
            col = field_map[f]
            hits = _search_single_field(query_lc, df[col], limit, score_cutoff, scorer)
            field_hits.append(hits)
        top = _merge_hits_per_field(field_hits, df, limit)
        out = []
        for idx, score in top:
            row = df.loc[idx]
            out.append({
                "index": int(idx),
                "first_name": row.first_name,
                "last_name": row.last_name,
                "full_name": row.full_name,
                "score": float(score),
                "extras": {}
            })
        return out

@register("rapidfuzz_token_set")
class RapidFuzzTokenSet(RapidFuzzRatio):
    def search(self, query, df, fields, limit, score_cutoff, params=None):
        scorer = _select_scorer("token_set")
        query_lc = query.lower()
        field_map = {"first": "first_lc", "last": "last_lc", "full": "full_lc"}
        field_hits = []
        for f in fields:
            col = field_map[f]
            hits = _search_single_field(query_lc, df[col], limit, score_cutoff, scorer)
            field_hits.append(hits)
        top = _merge_hits_per_field(field_hits, df, limit)
        out = []
        for idx, score in top:
            row = df.loc[idx]
            out.append({
                "index": int(idx),
                "first_name": row.first_name,
                "last_name": row.last_name,
                "full_name": row.full_name,
                "score": float(score),
                "extras": {}
            })
        return out
