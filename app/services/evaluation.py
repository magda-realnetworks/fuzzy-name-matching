from __future__ import annotations
from typing import List, Dict, Any, Optional
import pandas as pd

from app.services.dataset import DataContainer
from app.matchers.base import list_matchers, get_matcher


def _pick_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    lc = {c.lower().strip(): c for c in df.columns}
    for k in candidates:
        if k in lc:
            return lc[k]
    return None


def evaluate_pairs(
    container: DataContainer,
    field: str,                       # "first" | "last" | "full"
    pairs_df: pd.DataFrame,           # columns like mispelled/misspelled + correct
    methods: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    For each (mispelled, correct) row:
      - add ALL unique 'correct' values to a temporary copy of the chosen field DF
      - run each matcher with limit=1, score_cutoff=0
      - if top-1 full_name equals 'correct' (case-insensitive), count as correct
    Returns: [{"method": str, "total": int, "correct": int, "accuracy": float}, ...] (alphabetical by method)
    """
    # ---- detect columns (accept common spellings/aliases) ----
    left_col = _pick_col(pairs_df, ["mispelled", "misspelled", "typo", "query", "input"])
    right_col = _pick_col(pairs_df, ["correct", "target", "truth", "gold", "expected"])
    if not left_col or not right_col:
        raise ValueError(
            "Dataset must include two columns: one for the noisy value (e.g. 'mispelled' or 'misspelled') "
            "and one for the correct value (e.g. 'correct')."
        )

    pairs = pairs_df[[left_col, right_col]].dropna()
    if pairs.empty:
        return []

    pairs[left_col] = pairs[left_col].astype(str).str.strip()
    pairs[right_col] = pairs[right_col].astype(str).str.strip()

    # ---- choose base DF by field ----
    if field == "first":
        base = container.df_first[["name", "name_lc"]]
    elif field == "last":
        base = container.df_last[["name", "name_lc"]]
    elif field == "full":
        base = container.df_full[["name", "name_lc"]]
    else:
        raise ValueError(f"Unknown field: {field}")

    # ---- add 'correct' values temporarily to a copy ----
    add = pd.DataFrame({"name": pairs[right_col].drop_duplicates()})
    add["name_lc"] = add["name"].str.lower()
    print(add)
    df_eval = pd.concat([base, add], ignore_index=True)
    df_eval = df_eval.drop_duplicates(subset="name_lc", keep="first").reset_index(drop=True)

    # ---- run all/selected methods ----
    methods = sorted(methods or list_matchers())
    results: List[Dict[str, Any]] = []

    for m in methods:
        matcher = get_matcher(m)
        correct_cnt = 0
        total = int(pairs.shape[0])

        for _, row in pairs.iterrows():
            q = row[left_col]
            truth = row[right_col]
            hits = matcher.search(q, df_eval, ["name"], limit=1, score_cutoff=0, params={})
            if hits and hits[0]["full_name"].strip().casefold() == truth.strip().casefold():
                correct_cnt += 1

        acc = (correct_cnt / total * 100.0) if total else 0.0
        results.append({"method": m, "total": total, "correct": correct_cnt, "accuracy": acc})

    return results
