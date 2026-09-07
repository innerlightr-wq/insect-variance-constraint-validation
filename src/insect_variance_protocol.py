"""
Frozen protocol primitives for the insect-variance-constraint-validation
project (ROUND 0 -- design/provenance/freeze only).

This module implements pure, reusable functions needed to CONSTRUCT the
eligible-series table and to describe the corpus (Task 3, Task 6, Task 18).
It deliberately does NOT compute, fit, or report any association between a
constraint metric and the future outcome -- no correlation, no regression
coefficient, no p-value against the primary target. That is reserved for a
later, separately-frozen round. Functions here are individually unit-tested
(tests/test_insect_variance_protocol.py) against synthetic data with known
answers, never against the real corpus's outcome variable.

Primary corpus: van Klink et al. (2020), "A global database of long-term
changes in insect assemblages," KNB, DOI 10.5063/F11V5C9V. See
docs/DATA_PROVENANCE.md for exact file provenance/checksums.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

SERIES_KEY = ["DataSource_ID", "Plot_ID", "Stratum"]  # primary (abundance-only) unit key
MIN_TOTAL_POINTS = 10          # frozen, Task 6 -- see docs/HYPOTHESIS_PROTOCOL.md
MIN_WINDOW_POINTS = 5           # frozen, Task 6
STRATUM_MIN_SERIES = 30         # frozen, Task 14
STRATUM_MIN_STUDIES = 5         # frozen, Task 14


# =============================================================================
# Checksum validation (Task 2 / Task 19)
# =============================================================================
def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_of_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum(path: str, expected_md5: str) -> bool:
    return md5_of_file(path) == expected_md5


# =============================================================================
# TASK 7/8 -- power means and constraint metrics
# =============================================================================
def power_mean(x: np.ndarray, p: float) -> float:
    """M_p = (mean(x^p))^(1/p) for non-negative x, p != 0. Raises on
    negative values (power means with non-integer p are undefined for
    negative x) and on an empty input."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        raise ValueError("power_mean requires at least one value")
    if np.any(x < 0):
        raise ValueError("power_mean requires non-negative values")
    if p == 0:
        # geometric-mean limit; undefined if any x == 0
        if np.any(x == 0):
            return 0.0
        return float(np.exp(np.mean(np.log(x))))
    return float(np.mean(x ** p) ** (1.0 / p))


def coefficient_of_variation(x: np.ndarray) -> Optional[float]:
    """SD / mean. Returns None (undefined) if mean is exactly 0 or fewer
    than 2 observations."""
    x = np.asarray(x, dtype=float)
    if x.size < 2:
        return None
    m = float(np.mean(x))
    if m == 0.0:
        return None
    return float(np.std(x, ddof=1) / m)


def power_mean_ratio(x: np.ndarray, p: float, q: float = 1.0) -> Optional[float]:
    """D_{p/q} = M_p(x) / M_q(x). Frozen constraint-metric family
    (Candidate A: p=3,q=1; Candidate B: p=4,q=1). Returns None if M_q is
    exactly 0 (undefined ratio -- see docs/METRIC_PROPERTIES.md
    "undefined cases")."""
    x = np.asarray(x, dtype=float)
    denom = power_mean(x, q)
    if denom == 0.0:
        return None
    numer = power_mean(x, p)
    return numer / denom


def quantile_ratio(x: np.ndarray, q_hi: float = 0.90, q_lo: float = 0.50) -> Optional[float]:
    """Candidate C: robust tail/headroom statistic, Q_hi / Q_lo. Returns
    None if the low quantile is exactly 0."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        raise ValueError("quantile_ratio requires at least one value")
    lo = float(np.quantile(x, q_lo))
    hi = float(np.quantile(x, q_hi))
    if lo == 0.0:
        return None
    return hi / lo


def ols_trend_slope(years: np.ndarray, values: np.ndarray) -> Optional[float]:
    """Ordinary-least-squares slope of `values` regressed on `years`
    (calendar year as the single predictor, no intercept-forcing). Used
    identically for (a) the early-window trend, a conventional BASELINE
    predictor (Task 7), and (b) the late-window trend, the frozen PRIMARY
    OUTCOME (Task 5) -- same function, different window, never mixed.
    Returns None if fewer than 2 distinct year values are supplied (slope
    undefined)."""
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    if len(np.unique(years)) < 2:
        return None
    slope, _intercept = np.polyfit(years, values, 1)
    return float(slope)


# =============================================================================
# TASK 6 -- chronological split (no leakage)
# =============================================================================
def chronological_split(years: list[int]) -> tuple[list[int], list[int]]:
    """Splits a SORTED, DEDUPLICATED list of usable years into an early and
    late window: early = first ceil(n/2) years, late = remaining floor(n/2)
    years. This guarantees, for any n >= MIN_TOTAL_POINTS (10), both
    windows have >= MIN_WINDOW_POINTS (5) -- ceil(10/2)=5, floor(10/2)=5,
    and both halves only grow from there. No year appears in both windows;
    no late-window year is ever <= any early-window year (strict
    chronological ordering, not merely disjoint sets), which is the
    no-leakage guarantee."""
    ys = sorted(set(years))
    n = len(ys)
    n_early = math.ceil(n / 2)
    early, late = ys[:n_early], ys[n_early:]
    if early and late:
        assert max(early) < min(late), "chronological_split produced an out-of-order boundary"
    return early, late


# =============================================================================
# TASK 3/6 -- within-year duplicate handling (deterministic)
# =============================================================================
def aggregate_within_year(df: pd.DataFrame, value_col: str = "Number") -> pd.DataFrame:
    """Frozen, disclosed rule for duplicated years (multiple `Period`
    entries within one calendar year at the same DataSource_ID/Plot_ID/
    Stratum): SUM the value across periods, treated as repeated
    within-year censuses contributing to one annual total -- the standard
    ecological convention for combining sub-annual sampling occasions into
    an annual abundance index. A year with observations that are ALL null
    is left null (min_count=1), not silently coerced to zero -- a
    genuinely unsampled year must not be treated as an observed zero.
    Mean-aggregation was considered and rejected as the frozen default
    because summing preserves the total-effort interpretation of repeated
    censuses; this choice is disclosed, not hidden, and is not revisited
    based on any later result."""
    key = SERIES_KEY + ["Year"]
    out = (
        df.groupby(key)[value_col]
        .apply(lambda s: s.sum(min_count=1))
        .reset_index()
    )
    return out


# =============================================================================
# TASK 4/6 -- eligible-series construction
# =============================================================================
@dataclass
class SeriesEligibility:
    key: tuple
    n_usable_years: int
    early_years: list
    late_years: list
    eligible: bool
    exclusion_reason: Optional[str]


def build_yearly_abundance_table(raw_ab: pd.DataFrame) -> pd.DataFrame:
    """raw_ab: the raw InsectAbundanceBiomassData.csv rows already filtered
    to MetricAB == 'abundance' (Task 5 -- abundance is the primary
    analysis; biomass is reserved for sensitivity, never pooled with
    abundance in the same series)."""
    return aggregate_within_year(raw_ab, value_col="Number")


def eligibility_for_series(years_with_values: pd.Series) -> SeriesEligibility:
    """years_with_values: the Year values of a single series' rows that
    have a non-null annual aggregate (already filtered by the caller).
    Applies the frozen MIN_TOTAL_POINTS / MIN_WINDOW_POINTS rule (Task 6)."""
    usable_years = sorted(set(int(y) for y in years_with_values))
    n = len(usable_years)
    if n < MIN_TOTAL_POINTS:
        return SeriesEligibility((), n, [], [], False, f"fewer than {MIN_TOTAL_POINTS} usable years")
    early, late = chronological_split(usable_years)
    if len(early) < MIN_WINDOW_POINTS or len(late) < MIN_WINDOW_POINTS:
        return SeriesEligibility((), n, early, late, False, "window below minimum after split")
    return SeriesEligibility((), n, early, late, True, None)


def build_eligibility_table(yearly: pd.DataFrame) -> pd.DataFrame:
    """yearly: output of build_yearly_abundance_table (one row per
    DataSource_ID/Plot_ID/Stratum/Year, `Number` possibly null). Returns
    one row per candidate series with eligibility, window sizes, and
    exclusion reason. Does NOT compute or return any constraint metric or
    outcome value -- construction only."""
    usable = yearly.dropna(subset=["Number"])
    rows = []
    for key_vals, sub in usable.groupby(SERIES_KEY):
        elig = eligibility_for_series(sub["Year"])
        rows.append({
            "DataSource_ID": key_vals[0], "Plot_ID": key_vals[1], "Stratum": key_vals[2],
            "n_usable_years": elig.n_usable_years,
            "n_early": len(elig.early_years), "n_late": len(elig.late_years),
            "eligible": elig.eligible, "exclusion_reason": elig.exclusion_reason,
        })
    # also register candidate series that have ZERO usable years at all
    # (every observation null after aggregation) -- these never appear in
    # `usable`'s groupby, so they must be added back explicitly from the
    # full (pre-dropna) candidate key set.
    all_keys = yearly[SERIES_KEY].drop_duplicates()
    covered = {(r["DataSource_ID"], r["Plot_ID"], r["Stratum"]) for r in rows}
    for _, r in all_keys.iterrows():
        k = (r["DataSource_ID"], r["Plot_ID"], r["Stratum"])
        if k not in covered:
            rows.append({
                "DataSource_ID": k[0], "Plot_ID": k[1], "Stratum": k[2],
                "n_usable_years": 0, "n_early": 0, "n_late": 0,
                "eligible": False, "exclusion_reason": "zero usable years (all null after aggregation)",
            })
    return pd.DataFrame(rows)


# =============================================================================
# TASK 14 -- stratum adequacy gate (uses only eligibility counts, never outcome)
# =============================================================================
def stratum_adequacy(eligibility_table: pd.DataFrame) -> pd.DataFrame:
    elig = eligibility_table[eligibility_table["eligible"]]
    g = elig.groupby("Stratum").agg(
        n_series=("Plot_ID", "count"),
        n_studies=("DataSource_ID", "nunique"),
    ).reset_index()
    g["adequate_for_H3"] = (g["n_series"] >= STRATUM_MIN_SERIES) & (g["n_studies"] >= STRATUM_MIN_STUDIES)
    return g


# =============================================================================
# TASK 10 -- grouped validation folds (study-aware, deterministic)
# =============================================================================
def make_group_folds(groups: np.ndarray, n_splits: int, seed: int = 20260907) -> list:
    """Deterministic GroupKFold-style assignment: all rows sharing a group
    value (study id) land in the same fold. Uses sklearn's GroupKFold,
    which is itself deterministic given a fixed input order -- `seed` is
    accepted for interface symmetry with the permutation-based negative
    controls (Task 12) and to make the fold-generation call site
    self-documenting, even though GroupKFold's own assignment does not
    consume randomness."""
    from sklearn.model_selection import GroupKFold
    gkf = GroupKFold(n_splits=n_splits)
    dummy_X = np.zeros((len(groups), 1))
    return list(gkf.split(dummy_X, groups=groups))


# =============================================================================
# TASK 12 -- negative-control permutation primitives
# =============================================================================
def permute_within_group(values: np.ndarray, groups: np.ndarray, seed: int) -> np.ndarray:
    """NC1/NC2 primitive: permutes `values` independently WITHIN each
    distinct value of `groups` (e.g. within study), preserving the
    marginal distribution of `values` inside each group and the
    group-to-row assignment. A group of size 1 is unchanged (no valid
    permutation exists)."""
    values = np.asarray(values)
    groups = np.asarray(groups)
    out = values.copy()
    rng = np.random.default_rng(seed)
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        if len(idx) > 1:
            out[idx] = rng.permutation(values[idx])
    return out


def time_reversal_pseudo_future(early_values: np.ndarray, late_values: np.ndarray) -> tuple:
    """NC3 primitive: swaps which window plays the role of "predictor
    window" and which plays "outcome window" for the SAME series, so that
    the late window's own summary statistics predict the early window's
    own trend. Expected behavior under the frozen protocol (declared here,
    not left ambiguous, per Task 12): this is a diagnostic for
    directionality/leakage artifacts in the modeling pipeline, not a test
    of the scientific hypothesis in either direction -- a positive
    "prediction" here would indicate a pipeline artifact (e.g. a leaked
    time-invariant confound), not evidence for or against H1/H2."""
    return late_values, early_values
