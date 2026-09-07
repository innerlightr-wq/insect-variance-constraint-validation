#!/usr/bin/env python3
"""
H4 IMPLEMENTATION SKELETON -- frozen per docs/H4_PROTOCOL.md, commit
[this freeze commit]. FUNCTION DEFINITIONS ONLY. This module MUST NOT be
invoked against the real corpus's outcome data in this freeze round --
see docs/H4_PROTOCOL.md and results/H4_FREEZE_NO_PEEKING_AUDIT.md.
Every function here is exercised only against synthetic fixtures in
tests/test_h4_pipeline.py. No function in this module reads Round 1's
`outcome` column from the real corpus, computes a real H4 statistic, or
computes a real H4 p-value.

Deterministic structural functions (window construction, constituent-
series counting, C_g computation from historical-window abundance) are
permitted to operate on real dates/counts/historical CVs, mirroring
Round 2A's own no-peeking-compliant audits -- but this module's own
outcome-pairing and inference functions take already-built DataFrames as
arguments (dependency injection) rather than loading the real Round 1
outcome table themselves, specifically so this module can never
accidentally execute H4 against real data merely by being imported or
run.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from insect_variance_protocol import coefficient_of_variation, make_group_folds, permute_within_group  # noqa: E402
from round2a_cv_of_cv_feasibility import cv_of_cvs  # noqa: E402
from round1_execute import _fit_predict_fold, pooled_rmse  # noqa: E402  (reused, unchanged model spec)

MIN_CONSTITUENT_SERIES = 15   # frozen, docs/H4_PROTOCOL.md Sec.3
HISTORICAL_WINDOW_YEARS = 10   # frozen, docs/H4_PROTOCOL.md Sec.4
PERMUTATION_COUNT = 10_000     # frozen, docs/H4_PROTOCOL.md Sec.12
SEED = 20260907                # frozen, project convention
ALPHA = 0.05                    # frozen
MIN_STUDIES_FOR_INTERPRETABLE = 10   # frozen, docs/H4_PROTOCOL.md Sec.14

BASELINE_COLS = ["baseline_mean_log1p", "baseline_cv", "baseline_trend", "baseline_n", "baseline_span"]
AUGMENTED_COLS = BASELINE_COLS + ["C_g"]


# =============================================================================
# TASK 4/5 -- deterministic historical window construction (structural only)
# =============================================================================
def study_union_years(usable: pd.DataFrame, eligible_keys: list, study_id) -> list:
    """Sorted, deduplicated union of usable years across a study's
    Round-1-eligible series. Purely structural (dates/counts)."""
    study_keys = [k for k in eligible_keys if k[0] == study_id]
    years = set()
    for k in study_keys:
        sub = usable[
            (usable["DataSource_ID"] == k[0]) & (usable["Plot_ID"] == k[1]) & (usable["Stratum"] == k[2])
        ]
        years.update(sub["Year"].unique())
    return sorted(years)


def h4_historical_window(usable: pd.DataFrame, eligible_keys: list, study_id) -> Optional[dict]:
    """Design C, exactly as frozen: first 10 union-years = history,
    everything after = future. Returns None if the study has too few
    union-years to form both a window and a future period."""
    all_years = study_union_years(usable, eligible_keys, study_id)
    if len(all_years) < HISTORICAL_WINDOW_YEARS + 1:
        return None
    hist_years = all_years[:HISTORICAL_WINDOW_YEARS]
    fut_years = all_years[HISTORICAL_WINDOW_YEARS:]
    assert max(hist_years) < min(fut_years), "leakage: historical window overlaps future period"
    return {"hist_years": hist_years, "fut_years": fut_years}


# =============================================================================
# TASK 3/6 -- constituent-series eligibility and per-series CV (structural + historical CV only)
# =============================================================================
def constituent_series_for_window(usable: pd.DataFrame, eligible_keys: list, study_id, hist_years: list) -> list:
    """Series with >=2 usable observations inside hist_years. Structural
    eligibility check -- counts observations, never reads any value
    outside hist_years."""
    study_keys = [k for k in eligible_keys if k[0] == study_id]
    out = []
    for k in study_keys:
        sub = usable[
            (usable["DataSource_ID"] == k[0]) & (usable["Plot_ID"] == k[1]) & (usable["Stratum"] == k[2])
            & (usable["Year"].isin(hist_years))
        ]
        if sub.shape[0] >= 2:
            out.append(k)
    return out


def compute_C_g(usable: pd.DataFrame, constituent_keys: list, hist_years: list) -> Optional[float]:
    """C_g = SD_i(CV_i)/Mean_i(CV_i) over constituent series' CVs, each CV
    computed ONLY from that series' observations within hist_years. Never
    reads any value outside hist_years -- structurally cannot see the
    future."""
    cvs = []
    for k in constituent_keys:
        sub = usable[
            (usable["DataSource_ID"] == k[0]) & (usable["Plot_ID"] == k[1]) & (usable["Stratum"] == k[2])
            & (usable["Year"].isin(hist_years))
        ]
        cv = coefficient_of_variation(sub["Number"].values)
        if cv is not None and np.isfinite(cv):
            cvs.append(cv)
    if len(cvs) < MIN_CONSTITUENT_SERIES:
        return None
    return cv_of_cvs(np.array(cvs))


def study_h4_adequate(usable: pd.DataFrame, eligible_keys: list, study_id) -> dict:
    """Structural adequacy check for one study: window existence + >=15
    constituent series. Does NOT touch any future-period value."""
    window = h4_historical_window(usable, eligible_keys, study_id)
    if window is None:
        return {"adequate": False, "reason": "insufficient union-years for window + future"}
    constituents = constituent_series_for_window(usable, eligible_keys, study_id, window["hist_years"])
    if len(constituents) < MIN_CONSTITUENT_SERIES:
        return {"adequate": False, "reason": f"only {len(constituents)} constituent series (<{MIN_CONSTITUENT_SERIES})"}
    return {"adequate": True, "window": window, "constituent_keys": constituents}


# =============================================================================
# TASK 8/9 -- outcome eligibility filter (pure logic, no data loading)
# =============================================================================
def series_outcome_eligible(series_late_year_min: int, hist_years: list) -> bool:
    """docs/H4_PROTOCOL.md Sec.8-9: a series' Round-1 outcome may be used
    for H4 only if its own late window starts strictly after the study's
    H4 historical cutoff."""
    return series_late_year_min > max(hist_years)


# =============================================================================
# TASK 7/11 -- analysis-table assembly (DEPENDENCY-INJECTED, never loads real outcome itself)
# =============================================================================
def build_h4_row(study_id, C_g: float, baseline_row: dict, outcome_value: float) -> dict:
    """Assembles one H4 analysis-table row from ALREADY-COMPUTED,
    caller-supplied values. This function never reads a file, a column
    named 'outcome', or any real data -- it only combines arguments
    already provided by the caller. Real execution is deferred to a
    future, separately-approved round."""
    return {"DataSource_ID": study_id, "C_g": C_g, **baseline_row, "outcome": outcome_value}


# =============================================================================
# TASK 12 -- permutation and LOSO machinery (pure logic / synthetic-safe)
# =============================================================================
def permute_study_level_mapping(study_ids: np.ndarray, cg_by_study: dict, seed: int) -> dict:
    """Between-study permutation of the study-to-C_g mapping (docs/H4_PROTOCOL.md
    Sec.12.5): reassigns which study gets which OTHER study's C_g value.
    `study_ids` is the array of unique H4-eligible studies; `cg_by_study`
    maps study_id -> its own real C_g. Returns a new {study_id: C_g}
    mapping. Deterministic given `seed`."""
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(study_ids))
    cg_values = np.array([cg_by_study[i] for i in ids])
    permuted = rng.permutation(cg_values)
    return dict(zip(ids, permuted))


def loso_folds(groups: np.ndarray):
    """Leave-one-study-out: GroupKFold with n_splits == n_unique_groups."""
    n_groups = len(np.unique(groups))
    return make_group_folds(groups, n_splits=n_groups, seed=SEED)


def fit_and_pool_rmse(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float:
    """LOSO out-of-fold pooled RMSE, reusing Round 1's frozen, unchanged
    model spec (_fit_predict_fold: standardize-in-training-fold,
    OLS/Ridge-fallback)."""
    folds = loso_folds(groups)
    oof = np.full(len(y), np.nan)
    for train_idx, test_idx in folds:
        preds, _ = _fit_predict_fold(X[train_idx], y[train_idx], X[test_idx])
        oof[test_idx] = preds
    return pooled_rmse(y, oof)


def permutation_p_value(observed_delta_rmse: float, null_deltas: np.ndarray) -> float:
    """One-sided permutation p-value, docs/H4_PROTOCOL.md Sec.12.9-12.12."""
    return float((1 + np.sum(null_deltas >= observed_delta_rmse)) / (len(null_deltas) + 1))


# =============================================================================
# TASK 14 -- support-rule logic (pure, operates on already-computed statistics)
# =============================================================================
def h4_verdict(n_eligible_studies: int, delta_rmse: Optional[float], p_value: Optional[float],
               p_value_opposite: Optional[float] = None) -> str:
    """docs/H4_PROTOCOL.md Sec.14, applied mechanically to ALREADY-COMPUTED
    statistics passed in by the caller. This function does not compute
    delta_rmse or p_value itself."""
    if n_eligible_studies < MIN_STUDIES_FOR_INTERPRETABLE:
        return "UNINTERPRETABLE / BLOCKED"
    if delta_rmse is not None and p_value is not None and delta_rmse > 0 and p_value <= ALPHA:
        return "SUPPORTED"
    if p_value_opposite is not None and p_value_opposite <= ALPHA and delta_rmse is not None and delta_rmse < 0:
        return "DIRECTIONALLY OPPOSITE"
    return "NOT SUPPORTED"
