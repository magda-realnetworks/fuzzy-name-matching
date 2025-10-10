from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    data_path: Path = Field(default=Path(__file__).resolve().parents[2] / "data" / "celebtest_large_distinct.csv")
    preload_limit: int | None = None  # set to an int to cap rows during dev
    default_limit: int = 10
    max_limit: int = 100
    default_score_cutoff: int | None = None
    # columns
    col_first: str = "first_name"
    col_last: str = "last_name"
    # formats
    possible_formats: list[str] = ["raw", "Metaphone", "IPA"]
    default_format: str = "raw"

    class Config:
        env_prefix = "FUZZYAPP_"

settings = Settings()
