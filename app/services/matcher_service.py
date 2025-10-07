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
        # create one shared thread pool for CPU-bound operations
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
        methods: List[str],
        limit: int,
        score_cutoff: int,
        method_params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Run multiple matchers concurrently in separate threads.
        Returns a list of {method, hits}.
        """
        df = self._get_df_by_field(field)

        from concurrent.futures import as_completed
        futures = []
        results = []

        for m in methods:
            params = method_params.get(m, {})
            f = self.executor.submit(self._run_single_matcher, m, df, query, limit, score_cutoff, params)
            futures.append(f)

        for f in as_completed(futures):
            results.append(f.result())

        return results