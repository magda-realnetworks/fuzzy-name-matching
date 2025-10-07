from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from app.matchers.base import get_matcher
from app.services.dataset import DataContainer


class MatcherService:
    """
    Handles fuzzy matching across first, last, or full name datasets.
    """

    def __init__(self, data: DataContainer):
        self.data = data
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _get_df_by_field(self, field: str):
        if field == "first":
            return self.data.df_first
        elif field == "last":
            return self.data.df_last
        elif field == "full":
            return self.data.df_full
        else:
            raise ValueError(f"Unknown field: {field}")

    def _run_single_matcher(
        self, matcher_name: str, df, query: str,
        limit: int, score_cutoff: int, params: dict
    ):
        """ Run a single matcher on the given dataframe.
        Returns {"method": matcher_name, "hits": [...]}
        """
        matcher = get_matcher(matcher_name)
        hits = matcher.search(query, df, ["name"], limit, score_cutoff, params)
        return {"method": matcher_name, "hits": hits}

    def run_methods(
        self,
        query: str,
        field: str,
        methods: List[str] | None = None,
        limit: int | None = None,
        score_cutoff: int | None = None,
        method_params: Dict[str, Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Run multiple matchers concurrently in separate threads.
        Applies sensible defaults if args are missing.
        Returns list of {"method": matcher_name, "hits": [...]}, one per method.
        """
        from concurrent.futures import as_completed
        from app.matchers.base import list_matchers
        from app.core.config import settings

        # --- tidy normalization helpers (scoped to this function) ---
        def coerce_int(val, default):
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        def clamp(n, lo, hi):
            return max(lo, min(n, hi))

        # --- normalize inputs ---
        methods = methods or list_matchers()
        limit = clamp(coerce_int(limit, settings.default_limit), 1, settings.max_limit)
        score_cutoff = coerce_int(score_cutoff, settings.default_score_cutoff)
        method_params = method_params or {}

        df = self._get_df_by_field(field)

        futures = []
        results = []
        for m in methods:
            params = method_params.get(m, {})
            f = self.executor.submit(self._run_single_matcher, m, df, query, limit, score_cutoff, params)
            futures.append(f)

        for f in as_completed(futures):
            results.append(f.result())

        return results