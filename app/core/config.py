from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    data_path: Path = Field(default=Path(__file__).resolve().parents[2] / "data" / "names.csv")
    preload_limit: int | None = None  # set to an int to cap rows during dev
    default_limit: int = 10
    max_limit: int = 100
    default_score_cutoff: int = 70
    # columns
    col_first: str = "first_name"
    col_last: str = "last_name"

    class Config:
        env_prefix = "FUZZYAPP_"

settings = Settings()
