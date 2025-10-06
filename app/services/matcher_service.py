from app.core.config import settings
from app.matchers.base import get_matcher
from app.services.dataset import DataContainer
import pandas as pd

class MatcherService:
    def __init__(self, data: DataContainer):
        self.data = data

    def _get_df_by_field(self, field: str) -> pd.DataFrame:
        match field:
            case "first":
                return self.data.df_first
            case "last":
                return self.data.df_last
            case "full":
                return self.data.df_full
            case _:
                raise ValueError(f"Invalid field: {field}")

    def run_methods(
        self,
        query: str,
        field: str,
        methods: list[str],
        limit: int,
        score_cutoff: int,
        method_params: dict
    ):
        df = self._get_df_by_field(field)
        results = []
        for m in methods:
            matcher = get_matcher(m)
            params = method_params.get(m)
            hits = matcher.search(
                query=query,
                df=df,
                fields=["name"],  # always one field now
                limit=limit,
                score_cutoff=score_cutoff,
                params=params
            )
            results.append({ "method": m, "hits": hits })
        return results