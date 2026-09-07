#!/usr/bin/env python3
"""
ROUND 1 -- primary hypothesis execution against the protocol frozen at
commit 21e6992. Implements H1 (Task 4), H2 (Task 5), negative controls
(Task 6), Holm multiplicity (Task 7), the primary verdict (Task 8), H3
(Task 9), and descriptive benchmarks (Task 10).

Where the frozen protocol (docs/HYPOTHESIS_PROTOCOL.md) specifies a
concept but not every low-level implementation detail, the completion
chosen here is disclosed explicitly in-line (search "IMPLEMENTATION
COMPLETION" below) and was fixed BEFORE any result was inspected -- not
selected after seeing which choice produced a more favorable outcome.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from insect_variance_protocol import (  # noqa: E402
    make_group_folds, permute_within_group, coefficient_of_variation,
    power_mean_ratio, ols_trend_slope,
)
from round1_pipeline import build_modeling_table, BASELINE_COLS, CONSTRAINT_COLS, DATA_DIR, ENCODING  # noqa: E402

SEED = 20260907          # fixed, matches this project's own established convention
N_PERMUTATIONS = 2000    # frozen, docs/HYPOTHESIS_PROTOCOL.md Task 12
N_SPLITS = 10             # frozen
ALPHA = 0.05              # frozen
COND_THRESHOLD = 1e8      # frozen Ridge-fallback trigger, docs/HYPOTHESIS_PROTOCOL.md Task 11
RIDGE_ALPHA = 1.0         # frozen fallback alpha

H1_DIRECTION = {"D31": +1, "D41": +1, "Q9050": +1}  # frozen: higher metric -> less negative (better) outcome


# =============================================================================
# common analysis table
# =============================================================================
def common_table() -> pd.DataFrame:
    """IMPLEMENTATION COMPLETION (disclosed): M0 and M1 are compared on the
    IDENTICAL row set, so any RMSE difference reflects the added features,
    not a sample-composition change. Rows missing any baseline or
    constraint value (3 of 1129 -- undefined-metric edge cases documented
    in docs/METRIC_PROPERTIES.md) are excluded from H2 and from the common
    H1 comparison base. This was fixed before any model was fit."""
    tbl = build_modeling_table()
    needed = BASELINE_COLS + CONSTRAINT_COLS + ["outcome"]
    common = tbl.dropna(subset=needed).reset_index(drop=True)
    return common


# =============================================================================
# grouped OLS/Ridge fit with fallback, standardized within training fold
# =============================================================================
def _fit_predict_fold(X_train, y_train, X_test):
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0, ddof=0)
    std[std == 0] = 1.0
    Xtr = (X_train - mean) / std
    Xte = (X_test - mean) / std
    Xtr_design = np.column_stack([np.ones(len(Xtr)), Xtr])
    cond = np.linalg.cond(Xtr_design)
    fallback_used = cond > COND_THRESHOLD
    if not fallback_used:
        beta, *_ = np.linalg.lstsq(Xtr_design, y_train, rcond=None)
    else:
        # frozen fallback: Ridge, alpha=1.0, standardized features, intercept unpenalized
        from sklearn.linear_model import Ridge
        ridge = Ridge(alpha=RIDGE_ALPHA, fit_intercept=True)
        ridge.fit(Xtr, y_train)
        beta = np.concatenate([[ridge.intercept_], ridge.coef_])
    Xte_design = np.column_stack([np.ones(len(Xte)), Xte])
    preds = Xte_design @ beta
    return preds, fallback_used


def grouped_oof_predictions(X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits=N_SPLITS):
    folds = make_group_folds(groups, n_splits=n_splits, seed=SEED)
    oof = np.full(len(y), np.nan)
    fold_rmse, fold_fallback = [], []
    for train_idx, test_idx in folds:
        preds, fb = _fit_predict_fold(X[train_idx], y[train_idx], X[test_idx])
        oof[test_idx] = preds
        fold_fallback.append(bool(fb))
        fold_rmse.append(float(np.sqrt(np.mean((preds - y[test_idx]) ** 2))))
    return oof, fold_rmse, fold_fallback


def pooled_rmse(y, oof) -> float:
    return float(np.sqrt(np.mean((y - oof) ** 2)))


def pooled_r2(y, oof) -> float:
    ss_res = np.sum((y - oof) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


# =============================================================================
# TASK 4 -- H1 (cluster-robust OLS per metric, full eligible common sample)
# =============================================================================
def run_h1(df: pd.DataFrame) -> dict:
    """IMPLEMENTATION COMPLETION (disclosed): the frozen protocol asks for
    a coefficient, uncertainty interval, and raw p-value per metric. This
    is implemented as OLS of `outcome` on standardized baseline features +
    standardized constraint metric, with STUDY-CLUSTERED robust standard
    errors (cluster = DataSource_ID) -- the natural extension of the
    frozen grouping variable to inference, respecting the same
    across-series-within-study dependence the grouped CV design already
    respects. Fixed before any coefficient was inspected."""
    results = {}
    X_base = df[BASELINE_COLS].values.astype(float)
    Xb_std = (X_base - X_base.mean(axis=0)) / X_base.std(axis=0, ddof=0)
    y = df["outcome"].values.astype(float)
    groups = df["DataSource_ID"].values

    for metric in CONSTRAINT_COLS:
        m = df[metric].values.astype(float)
        m_std = (m - m.mean()) / m.std(ddof=0)
        X = np.column_stack([Xb_std, m_std])
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
        coef_idx = X.shape[1] - 1  # last column = the metric
        coef = float(model.params[coef_idx])
        se = float(model.bse[coef_idx])
        ci_lo, ci_hi = model.conf_int(alpha=ALPHA)[coef_idx]
        p_raw = float(model.pvalues[coef_idx])
        expected_sign = H1_DIRECTION[metric]
        observed_sign = int(np.sign(coef)) if coef != 0 else 0
        matches_direction = observed_sign == expected_sign
        results[metric] = {
            "n": int(len(y)), "n_studies": int(df["DataSource_ID"].nunique()),
            "coefficient_standardized": coef, "se_cluster_robust": se,
            "ci_95": [float(ci_lo), float(ci_hi)],
            "raw_p_value": p_raw,
            "expected_direction": "positive" if expected_sign > 0 else "negative",
            "observed_direction": "positive" if observed_sign > 0 else ("negative" if observed_sign < 0 else "zero"),
            "direction_matches_frozen_prediction": bool(matches_direction),
        }
    return results


# =============================================================================
# TASK 5 -- H2 (grouped OOF RMSE/R^2, M0 vs M1)
# =============================================================================
def run_h2(df: pd.DataFrame) -> dict:
    y = df["outcome"].values.astype(float)
    groups = df["DataSource_ID"].values
    X0 = df[BASELINE_COLS].values.astype(float)
    X1 = df[BASELINE_COLS + CONSTRAINT_COLS].values.astype(float)

    oof0, fold_rmse0, fb0 = grouped_oof_predictions(X0, y, groups)
    oof1, fold_rmse1, fb1 = grouped_oof_predictions(X1, y, groups)

    rmse0, rmse1 = pooled_rmse(y, oof0), pooled_rmse(y, oof1)
    r2_0, r2_1 = pooled_r2(y, oof0), pooled_r2(y, oof1)
    delta_rmse = rmse0 - rmse1
    delta_r2 = r2_1 - r2_0
    fold_delta = [a - b for a, b in zip(fold_rmse0, fold_rmse1)]
    n_folds_favoring_m1 = int(sum(1 for d in fold_delta if d > 0))

    return {
        "n": int(len(y)), "n_folds": N_SPLITS,
        "M0_pooled_oof_rmse": rmse0, "M1_pooled_oof_rmse": rmse1,
        "delta_rmse_M0_minus_M1": delta_rmse,
        "M0_pooled_oof_r2": r2_0, "M1_pooled_oof_r2": r2_1,
        "delta_r2_M1_minus_M0": delta_r2,
        "fold_rmse_M0": fold_rmse0, "fold_rmse_M1": fold_rmse1,
        "fold_delta_rmse": fold_delta,
        "n_folds_favoring_M1": n_folds_favoring_m1,
        "median_fold_delta_rmse": float(np.median(fold_delta)),
        "ridge_fallback_used_any_fold_M0": bool(any(fb0)),
        "ridge_fallback_used_any_fold_M1": bool(any(fb1)),
        "_oof0": oof0, "_oof1": oof1,  # retained in-memory for NC use, stripped before JSON write
    }


# =============================================================================
# TASK 6 -- negative controls (targeting H2's delta_rmse, per
# docs/HYPOTHESIS_PROTOCOL.md Sec.9's own stated rationale)
# =============================================================================
def nc1_within_study_constraint_permutation(df: pd.DataFrame, observed_delta_rmse: float, n_perm=N_PERMUTATIONS) -> dict:
    y = df["outcome"].values.astype(float)
    groups = df["DataSource_ID"].values
    X0 = df[BASELINE_COLS].values.astype(float)
    C = df[CONSTRAINT_COLS].values.astype(float)
    idx = np.arange(len(df))

    # M0 is unaffected by permuting the constraint metrics -- compute once.
    oof0, _, _ = grouped_oof_predictions(X0, y, groups)
    rmse0 = pooled_rmse(y, oof0)

    null_deltas = np.empty(n_perm)
    for b in range(n_perm):
        perm_idx = permute_within_group(idx, groups, seed=SEED + b)
        C_perm = C[perm_idx]
        X1_perm = np.column_stack([X0, C_perm])
        oof1_perm, _, _ = grouped_oof_predictions(X1_perm, y, groups)
        rmse1_perm = pooled_rmse(y, oof1_perm)
        null_deltas[b] = rmse0 - rmse1_perm

    p_one_sided = float((np.sum(null_deltas >= observed_delta_rmse) + 1) / (n_perm + 1))
    return {
        "n_permutations": n_perm, "observed_delta_rmse": observed_delta_rmse,
        "null_mean": float(null_deltas.mean()), "null_sd": float(null_deltas.std(ddof=1)),
        "null_q95": float(np.quantile(null_deltas, 0.95)),
        "empirical_one_sided_p": p_one_sided,
        "expected_under_true_null": "delta_rmse collapses toward the null distribution above",
    }


def nc2_within_study_outcome_permutation(df: pd.DataFrame, observed_delta_rmse: float, n_perm=N_PERMUTATIONS) -> dict:
    y = df["outcome"].values.astype(float)
    groups = df["DataSource_ID"].values
    X0 = df[BASELINE_COLS].values.astype(float)
    X1 = df[BASELINE_COLS + CONSTRAINT_COLS].values.astype(float)

    null_deltas = np.empty(n_perm)
    for b in range(n_perm):
        y_perm = permute_within_group(y, groups, seed=SEED + 10_000 + b)
        oof0_perm, _, _ = grouped_oof_predictions(X0, y_perm, groups)
        oof1_perm, _, _ = grouped_oof_predictions(X1, y_perm, groups)
        null_deltas[b] = pooled_rmse(y_perm, oof0_perm) - pooled_rmse(y_perm, oof1_perm)

    p_one_sided = float((np.sum(null_deltas >= observed_delta_rmse) + 1) / (n_perm + 1))
    return {
        "n_permutations": n_perm, "observed_delta_rmse": observed_delta_rmse,
        "null_mean": float(null_deltas.mean()), "null_sd": float(null_deltas.std(ddof=1)),
        "null_q95": float(np.quantile(null_deltas, 0.95)),
        "empirical_one_sided_p": p_one_sided,
        "expected_under_true_null": "delta_rmse collapses toward the null distribution above",
    }


def nc3_time_reversal(full_table_with_reversed: pd.DataFrame) -> dict:
    y = full_table_with_reversed["outcome_reversed"].values.astype(float)
    groups = full_table_with_reversed["DataSource_ID"].values
    X0 = full_table_with_reversed[[c + "_rev" for c in BASELINE_COLS]].values.astype(float)
    X1 = full_table_with_reversed[[c + "_rev" for c in BASELINE_COLS] + [c + "_rev" for c in CONSTRAINT_COLS]].values.astype(float)
    oof0, _, _ = grouped_oof_predictions(X0, y, groups)
    oof1, _, _ = grouped_oof_predictions(X1, y, groups)
    rmse0, rmse1 = pooled_rmse(y, oof0), pooled_rmse(y, oof1)
    delta = rmse0 - rmse1
    return {
        "n": int(len(y)),
        "reversed_M0_rmse": rmse0, "reversed_M1_rmse": rmse1,
        "reversed_delta_rmse": delta,
        "interpretation": (
            "diagnostic only, not evidence for or against H1/H2 in either "
            "direction. A large positive reversed_delta_rmse here would "
            "flag a leaked time-invariant confound in the pipeline; it "
            "does not, per the frozen protocol, count toward or against "
            "the primary verdict."
        ),
    }


def build_reversed_table() -> pd.DataFrame:
    """Builds the NC3 table by swapping which chronological half plays
    predictor vs. outcome role, reusing round1_pipeline.series_row's
    logic with early/late swapped."""
    from insect_variance_protocol import build_yearly_abundance_table, build_eligibility_table, chronological_split
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding=ENCODING)
    abund = ab[ab["MetricAB"] == "abundance"].copy()
    yearly = build_yearly_abundance_table(abund)
    eligibility = build_eligibility_table(yearly)
    eligible = eligibility[eligibility["eligible"]]
    usable = yearly.dropna(subset=["Number"])

    rows = []
    for _, r in eligible.iterrows():
        key = (r["DataSource_ID"], r["Plot_ID"], r["Stratum"])
        sub = usable[
            (usable["DataSource_ID"] == key[0]) & (usable["Plot_ID"] == key[1]) & (usable["Stratum"] == key[2])
        ].sort_values("Year")
        years_all = sorted(sub["Year"].unique())
        early_years, late_years = chronological_split(years_all)
        # REVERSED: late window is now the "predictor" window, early is the "outcome" window
        pred_win = sub[sub["Year"].isin(late_years)]
        out_win = sub[sub["Year"].isin(early_years)]
        px = pred_win["Number"].values.astype(float)
        ox = out_win["Number"].values.astype(float)
        row = {
            "DataSource_ID": key[0],
            "baseline_mean_log1p_rev": float(np.mean(np.log1p(px))),
            "baseline_cv_rev": coefficient_of_variation(px),
            "baseline_trend_rev": ols_trend_slope(pred_win["Year"].values, np.log1p(px)),
            "baseline_n_rev": len(px),
            "baseline_span_rev": int(max(late_years) - min(late_years)),
            "D31_rev": power_mean_ratio(px, 3, 1),
            "D41_rev": power_mean_ratio(px, 4, 1),
            "Q9050_rev": None,
            "outcome_reversed": ols_trend_slope(out_win["Year"].values, np.log1p(ox)),
        }
        from insect_variance_protocol import quantile_ratio
        row["Q9050_rev"] = quantile_ratio(px, 0.90, 0.50)
        rows.append(row)
    tbl = pd.DataFrame(rows)
    needed = [c + "_rev" for c in BASELINE_COLS + CONSTRAINT_COLS] + ["outcome_reversed"]
    return tbl.dropna(subset=needed).reset_index(drop=True)


# =============================================================================
# TASK 7 -- Holm correction
# =============================================================================
def holm_correction(raw_p: dict) -> dict:
    items = sorted(raw_p.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted = {}
    running_max = 0.0
    for i, (name, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running_max = max(running_max, adj)
        adjusted[name] = running_max
    return adjusted


# =============================================================================
# TASK 9 -- H3 secondary stratum analysis (adequate strata only)
# =============================================================================
ADEQUATE_STRATA = ["Air", "Water", "Herb layer", "Soil surface"]


def run_h3(df: pd.DataFrame) -> dict:
    results = {}
    for stratum in ADEQUATE_STRATA:
        sub = df[df["Stratum"] == stratum].reset_index(drop=True)
        n_series = int(sub.shape[0])
        n_studies = int(sub["DataSource_ID"].nunique())

        X_base = sub[BASELINE_COLS].values.astype(float)
        Xb_std = (X_base - X_base.mean(axis=0)) / X_base.std(axis=0, ddof=0)
        y = sub["outcome"].values.astype(float)
        groups = sub["DataSource_ID"].values

        metric_effects = {}
        for metric in CONSTRAINT_COLS:
            m = sub[metric].values.astype(float)
            m_std = (m - m.mean()) / m.std(ddof=0)
            X = sm.add_constant(np.column_stack([Xb_std, m_std]))
            cluster_ok = n_studies >= 20  # disclosed threshold for trusting cluster-robust SEs
            if cluster_ok:
                model = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
            else:
                model = sm.OLS(y, X).fit()  # non-clustered, flagged below -- too few clusters for reliable cluster-robust SEs
            coef_idx = X.shape[1] - 1
            coef = float(model.params[coef_idx])
            p = float(model.pvalues[coef_idx])
            metric_effects[metric] = {
                "coefficient_standardized": coef, "raw_p_value": p,
                "cluster_robust_se_used": cluster_ok,
                "direction": "positive" if coef > 0 else ("negative" if coef < 0 else "zero"),
                "matches_frozen_H1_direction": (np.sign(coef) == H1_DIRECTION[metric]) if coef != 0 else False,
            }

        n_splits = min(5, n_studies)
        X0 = sub[BASELINE_COLS].values.astype(float)
        X1 = sub[BASELINE_COLS + CONSTRAINT_COLS].values.astype(float)
        oof0, _, _ = grouped_oof_predictions(X0, y, groups, n_splits=n_splits)
        oof1, _, _ = grouped_oof_predictions(X1, y, groups, n_splits=n_splits)
        rmse0, rmse1 = pooled_rmse(y, oof0), pooled_rmse(y, oof1)

        results[stratum] = {
            "n_series": n_series, "n_studies": n_studies,
            "cv_n_splits_used": n_splits,
            "metric_effects": metric_effects,
            "M0_rmse": rmse0, "M1_rmse": rmse1, "delta_rmse": rmse0 - rmse1,
        }

    # direction consistency across strata, per metric
    direction_consistency = {}
    for metric in CONSTRAINT_COLS:
        signs = [np.sign(results[s]["metric_effects"][metric]["coefficient_standardized"]) for s in ADEQUATE_STRATA]
        direction_consistency[metric] = {
            "signs_by_stratum": {s: int(sg) for s, sg in zip(ADEQUATE_STRATA, signs)},
            "all_same_sign": bool(len(set(signs)) == 1),
        }
    return {"per_stratum": results, "direction_consistency_across_strata": direction_consistency,
            "excluded_strata": ["Trees", "Underground"],
            "excluded_reason": "fail the frozen Task 14 adequacy gate (>=30 series AND >=5 studies) -- see docs/HYPOTHESIS_PROTOCOL.md Sec.6"}


# =============================================================================
# TASK 10 -- descriptive benchmarks (CV-of-CVs, Taylor's Law) -- NOT evidence for H1/H2
# =============================================================================
def descriptive_cv_of_cvs() -> dict:
    """Reproduces the exact Round 0 computation (docs/CV_OF_CV_INTERPRETATION.md):
    all 1,613 candidate abundance series, full usable-year span, raw scale."""
    from insect_variance_protocol import build_yearly_abundance_table, SERIES_KEY
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding=ENCODING)
    abund = ab[ab["MetricAB"] == "abundance"].copy()
    yearly = build_yearly_abundance_table(abund)
    usable = yearly.dropna(subset=["Number"])
    cvs = []
    for key, sub in usable.groupby(SERIES_KEY):
        cv = coefficient_of_variation(sub["Number"].values)
        if cv is not None and np.isfinite(cv):
            cvs.append(cv)
    cvs = np.array(cvs)
    return {
        "label": "DESCRIPTIVE / BENCHMARK -- not evidence for H1/H2",
        "n_series": int(len(cvs)),
        "mean_cv": float(cvs.mean()), "sd_cv": float(cvs.std(ddof=1)),
        "cv_of_cvs": float(cvs.std(ddof=1) / cvs.mean()),
        "median_cv": float(np.median(cvs)),
        "range_cv": [float(cvs.min()), float(cvs.max())],
        "caveat": "finite empirical dispersion != ecological upper bound -- "
                  "see docs/CV_OF_CV_INTERPRETATION.md; this number is not "
                  "re-interpreted here.",
    }


def descriptive_taylors_law() -> dict:
    """log-log OLS of within-series variance on within-series mean, over
    each eligible series' FULL usable-year span (not the early/late
    split -- Taylor's Law is a whole-series descriptive benchmark, kept
    analytically separate from H1/H2 per docs/SCOPE_AND_FUTURE_WORK.md)."""
    from insect_variance_protocol import build_yearly_abundance_table, build_eligibility_table, SERIES_KEY
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding=ENCODING)
    abund = ab[ab["MetricAB"] == "abundance"].copy()
    yearly = build_yearly_abundance_table(abund)
    eligibility = build_eligibility_table(yearly)
    eligible_keys = eligibility[eligibility["eligible"]][["DataSource_ID", "Plot_ID", "Stratum"]]
    usable = yearly.dropna(subset=["Number"])

    means, variances = [], []
    for _, r in eligible_keys.iterrows():
        sub = usable[
            (usable["DataSource_ID"] == r["DataSource_ID"]) & (usable["Plot_ID"] == r["Plot_ID"]) & (usable["Stratum"] == r["Stratum"])
        ]
        x = sub["Number"].values.astype(float)
        mean_x, var_x = float(np.mean(x)), float(np.var(x, ddof=1))
        if mean_x > 0 and var_x > 0:
            means.append(mean_x)
            variances.append(var_x)
    log_mean = np.log(np.array(means))
    log_var = np.log(np.array(variances))
    X = sm.add_constant(log_mean)
    model = sm.OLS(log_var, X).fit()
    b = float(model.params[1])
    a_log = float(model.params[0])
    r2 = float(model.rsquared)
    n_excluded = int(len(eligible_keys) - len(means))
    return {
        "label": "DESCRIPTIVE / BENCHMARK -- not evidence for H1/H2",
        "n_series_used": len(means), "n_excluded_zero_mean_or_variance": n_excluded,
        "taylor_b_slope": b, "taylor_log_a_intercept": a_log, "r_squared": r2,
        "manuscript_reported_b": 1.96, "manuscript_reported_r2": 0.96,
        "note": "independently computed from this project's own eligible-series "
                "table; not assumed to match the manuscript's reported values.",
    }
