import panphon.distance as ppd
from typing import Optional

_dst = ppd.Distance()

def _seg_len(s: str) -> int:
    """Number of IPA segments (phones) per PanPhon’s feature model."""
    return len(_dst.fm.ipa_segs(s))

def _len_for_norm(a: str, b: str, by: str = "segments") -> int:
    """
    Denominator for length-normalized similarities.
    by='segments' uses IPA phone count (recommended);
    by='chars' uses raw string length.
    """
    if by == "chars":
        return max(len(a), len(b))
    return max(_seg_len(a), _seg_len(b))

def _apply_cutoff(sim: float, score_cutoff: Optional[float]) -> float:
    """
    If score_cutoff is provided and sim < score_cutoff, return 0.0.
    Otherwise return sim unchanged.
    """
    if score_cutoff is None:
        return sim
    return sim if sim >= score_cutoff else 0.0

def _sim_length_norm(d: float, denom: int, score_cutoff: Optional[float] = None) -> float:
    """Similarity in [0,1] via 1 - d/denom (clamped), with optional cutoff."""
    if denom <= 0:
        sim = 1.0
    else:
        ratio = min(d / denom, 1.0)
        sim = 1.0 - ratio
    return _apply_cutoff(sim, score_cutoff)

def _sim_inverse(d: float, score_cutoff: Optional[float] = None) -> float:
    """Similarity in [0,1] via 1/(1+d); good for unbounded distances, with optional cutoff."""
    sim = 1.0 / (1.0 + float(d))
    return _apply_cutoff(sim, score_cutoff)

# --- 1) fast_levenshtein_distance (on raw strings) ---------------------------

def sim_fast_levenshtein(
    a: str,
    b: str,
    norm_by: str = "segments",
    score_cutoff: Optional[float] = None
) -> float:
    """
    Similarity in [0,1] based on PanPhon's fast Levenshtein over characters.
    Normalized by max length (chars or segments). Applies score_cutoff if provided.
    """
    d = _dst.fast_levenshtein_distance(a, b)
    denom = _len_for_norm(a, b, by=norm_by)
    return _sim_length_norm(d, denom, score_cutoff=score_cutoff)

# --- 2) dolgo_prime_distance (sound-class edit distance) ---------------------

def sim_dolgo_prime(
    a: str,
    b: str,
    norm_by: str = "segments",
    score_cutoff: Optional[float] = None
) -> float:
    """
    Similarity in [0,1] using Dolgopolsky PRIME sound classes.
    Normalized by max length (chars or segments). Applies score_cutoff if provided.
    """
    d = _dst.dolgo_prime_distance(a, b)
    denom = _len_for_norm(a, b, by=norm_by)
    return _sim_length_norm(d, denom, score_cutoff=score_cutoff)

# --- 3) feature_edit_distance (feature-based edit costs) ---------------------

def sim_feature_edit(
    a: str,
    b: str,
    weighted: bool = True,
    similarity: str = "inverse",
    norm_by: str = "segments",
    score_cutoff: Optional[float] = None
) -> float:
    """
    Similarity in [0,1] using PanPhon feature-based edit distance.
      - weighted=True  -> weighted_feature_edit_distance
      - weighted=False -> feature_edit_distance
    Similarity modes:
      - 'inverse': 1/(1+d)  (good for unbounded feature distances)
      - 'length':  1 - d/denom (denom via norm_by)
    Applies score_cutoff if provided.
    """
    d = (_dst.weighted_feature_edit_distance(a, b)
         if weighted else _dst.feature_edit_distance(a, b))

    if similarity == "inverse":
        return _sim_inverse(d, score_cutoff=score_cutoff)
    elif similarity == "length":
        denom = _len_for_norm(a, b, by=norm_by)
        return _sim_length_norm(d, denom, score_cutoff=score_cutoff)
    else:
        raise ValueError("similarity must be 'inverse' or 'length'")
