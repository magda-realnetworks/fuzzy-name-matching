from dataclasses import dataclass
import pandas as pd
from app.core.config import settings
import jellyfish
from g2p_en import G2p
import nltk
nltk.download('averaged_perceptron_tagger_eng')

g2p = G2p()

@dataclass
class DataContainer:
    df_first: pd.DataFrame
    df_last: pd.DataFrame
    df_full: pd.DataFrame

def load_dataset(path=None, limit=None) -> DataContainer:
    path = path or settings.data_path
    df = pd.read_csv(path, nrows=limit)
    col_first, col_last = settings.col_first, settings.col_last

    df[col_first] = df[col_first].fillna("").astype(str).str.strip()
    df[col_last] = df[col_last].fillna("").astype(str).str.strip()
    df["full_name"] = (df[col_first] + " " + df[col_last]).str.strip()

    # Deduplicated per-column dataframes
    df_first = pd.DataFrame({ "name": df[col_first].drop_duplicates().sort_values() })
    df_last = pd.DataFrame({ "name": df[col_last].drop_duplicates().sort_values() })
    df_full = pd.DataFrame({ "name": df["full_name"].drop_duplicates().sort_values() })

    for d in [df_first, df_last, df_full]:
        d["name_lc"] = d["name"].str.lower()
        d["name_lc_metaphone"] = d["name_lc"].apply(lambda x: jellyfish.metaphone(x))
        d["name_lc_ipa"] = d["name_lc"].apply(lambda x: "".join(g2p(x)))      # add transformation logic later
        d.to_csv("tmp/debug.csv", index=False)  # DEBUG
    return DataContainer(df_first=df_first, df_last=df_last, df_full=df_full)
