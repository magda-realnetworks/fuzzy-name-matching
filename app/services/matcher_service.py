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

    def _run_single_matcher_single_format(
        self, matcher_name: str, df, query: str, format: str,
        limit: int, score_cutoff: int, params: dict
    ):
        """Run one matcher and return {'method': name, 'duration_ms': float, 'hits': [...]}."""
        from time import perf_counter
        matcher = get_matcher(matcher_name)
        t0 = perf_counter()
        hits = matcher.search(query, df, format, limit, score_cutoff, params)
        duration_ms = (perf_counter() - t0) * 1000.0
        return {"method": matcher_name, "duration_ms": duration_ms, "hits": hits}

    def run_methods(
        self,
        query: str,
        field: str,
        methods: List[str] | None = None,
        formats: list[str] | None = None,
        limit: int | None = None,
        score_cutoff: int | None = None,
        method_params: Dict[str, Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Run multiple matchers concurrently in separate threads.
        Applies sensible defaults if args are missing.
        Returns list of {"method": matcher_name, "hits": [...]}, one per method.
        Deterministic result order (alphabetical by method name).
        """
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
        methods = sorted(methods)  # enforce deterministic alphabetical order
        limit = clamp(coerce_int(limit, settings.default_limit), 1, settings.max_limit)
        score_cutoff = coerce_int(score_cutoff, settings.default_score_cutoff)
        method_params = method_params or {}

        df = self._get_df_by_field(field)

        # start all tasks concurrently
        results=[]
        for format in formats:
            futures = {
                m: self.executor.submit(
                    self._run_single_matcher_single_format,
                    m, df, query, format, limit, score_cutoff, method_params.get(m, {})
                )
                for m in methods
            }

            # collect results in the fixed order
            format_results = [futures[m].result() for m in methods]
            results.append({"format": format, "results": format_results})
        return results