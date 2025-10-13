from dataclasses import dataclass
import pandas as pd
from app.core.config import settings
import jellyfish
from g2p_en import G2p
import nltk
nltk.download('averaged_perceptron_tagger_eng')

arpabet_to_ipa = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɝ", "EY": "eɪ",
    "F": "f", "G": "ɡ", "HH": "h", "IH": "ɪ", "IY": "i", "JH": "dʒ", "K": "k",
    "L": "l", "M": "m", "N": "n", "NG": "ŋ", "OW": "oʊ", "OY": "ɔɪ",
    "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ", "T": "t", "TH": "θ",
    "UH": "ʊ", "UW": "u", "V": "v", "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ"
}

def arpabet_seq_to_ipa(arpas):
    ipa = []
    for sym in arpas:
        if sym == " ":
            continue
        # strip stress digits (e.g., IH1 -> IH)
        base = ''.join([c for c in sym if not c.isdigit()])
        ipa.append(arpabet_to_ipa.get(base, base.lower()))
    return ''.join(ipa)


def name_to_ipa_g2p_en(name: str) -> str:
    arpas = g2p(name)  # returns tokens incl. spaces and ARPABET with stress
    return arpabet_seq_to_ipa(arpas)

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
        d["name_lc_metaphone"] = d["name_lc"].apply(jellyfish.metaphone)
        d["name_lc_arpabet"] = d["name_lc"].apply(lambda x: "".join(g2p(x)))      # add transformation logic later
        d["name_lc_ipa"]=d["name_lc"].apply(name_to_ipa_g2p_en)  # add transformation logic later
        d.to_csv("tmp/debug.csv", index=False)  # DEBUG
    return DataContainer(df_first=df_first, df_last=df_last, df_full=df_full)
