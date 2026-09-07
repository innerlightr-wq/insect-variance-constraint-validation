#!/usr/bin/env python3
"""
ROUND 2A -- CV-of-CVs early-warning FEASIBILITY audit. Structural/support
audit only. NO function in this module reads, computes, or references any
future/late-window outcome value, any predictor-outcome association,
correlation, regression, AUC, RMSE-against-outcome, or p-value for a
predictive association. See docs/CV_OF_CV_EARLY_WARNING_CONCEPT.md and
results/ROUND2A_NO_PEEKING_AUDIT.md.

Every function here operates on: (a) Year/Plot_ID/DataSource_ID/Stratum as
counts and dates, (b) historical-window abundance CVs used only to study
the CV-of-CVs ESTIMATOR's own numerical behavior (never compared to any
later value), and (c) study/plot metadata fields for a confounding audit.
"""
from __future__ import annotations

import itertools
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from insect_variance_protocol import (  # noqa: E402
    build_yearly_abundance_table, build_eligibility_table, coefficient_of_variation,
    SERIES_KEY,
)

DATA_DIR = "data/raw/insect_knb"
ENCODING = "latin-1"

SERIES_COUNT_THRESHOLDS = [2, 3, 5, 10, 15, 20, 30, 50]
CONTEMPORANEOUS_THRESHOLDS = [2, 3, 5, 10, 15, 20]
RUN_LENGTH_THRESHOLDS = [3, 5, 7, 10]
WINDOW_LENGTHS = [3, 5, 7, 10]
WINDOW_SERIES_THRESHOLDS = [3, 5, 10, 20]
GROUP_SIZES = [3, 5, 10, 15, 20, 30]
CHANGE_MIN_WINDOWS = [3, 4, 5]
BOOTSTRAP_RESAMPLES = 1000   # frozen BEFORE running Task 6, per the round's own instruction
BOOTSTRAP_SEED = 20260907


# =============================================================================
# loading (reuses Round 0/1 primitives verbatim -- no new extraction rule)
# =============================================================================
def load_tables() -> dict:
    return {
        "DataSources": pd.read_csv(os.path.join(DATA_DIR, "DataSources.csv"), encoding=ENCODING),
        "PlotData": pd.read_csv(os.path.join(DATA_DIR, "PlotData.csv"), encoding=ENCODING),
        "SampleData": pd.read_csv(os.path.join(DATA_DIR, "SampleData.csv"), encoding=ENCODING),
    }


def load_usable_and_eligibility():
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding=ENCODING)
    abund = ab[ab["MetricAB"] == "abundance"].copy()
    yearly = build_yearly_abundance_table(abund)
    eligibility = build_eligibility_table(yearly)
    usable = yearly.dropna(subset=["Number"])
    eligible = eligibility[eligibility["eligible"]]
    return usable, eligibility, eligible


def _series_years(usable: pd.DataFrame, key: tuple) -> list:
    sub = usable[
        (usable["DataSource_ID"] == key[0]) & (usable["Plot_ID"] == key[1]) & (usable["Stratum"] == key[2])
    ]
    return sorted(sub["Year"].unique())


# =============================================================================
# TASK 3 -- study-level multi-series support
# =============================================================================
def study_multiseries_support(usable: pd.DataFrame, eligibility: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ds_id, cand_g in eligibility.groupby("DataSource_ID"):
        n_candidate = int(cand_g.shape[0])
        elig_g = cand_g[cand_g["eligible"]]
        n_eligible = int(elig_g.shape[0])
        study_usable = usable[usable["DataSource_ID"] == ds_id]
        n_plots = int(study_usable["Plot_ID"].nunique())
        years = sorted(study_usable["Year"].unique())
        year_min = int(min(years)) if years else None
        year_max = int(max(years)) if years else None
        n_unique_years = len(years)

        if n_eligible > 0:
            obs_counts = []
            year_presence = {y: 0 for y in years}
            for _, r in elig_g.iterrows():
                key = (r["DataSource_ID"], r["Plot_ID"], r["Stratum"])
                sy = _series_years(usable, key)
                obs_counts.append(len(sy))
                for y in sy:
                    year_presence[y] += 1
            median_obs = float(np.median(obs_counts))
            mean_year_coverage_fraction = float(
                np.mean([v / n_eligible for v in year_presence.values()])
            ) if year_presence else 0.0
        else:
            median_obs, mean_year_coverage_fraction = None, None

        rows.append({
            "DataSource_ID": ds_id, "n_candidate_series": n_candidate, "n_eligible_series": n_eligible,
            "n_unique_plots": n_plots, "year_min": year_min, "year_max": year_max,
            "n_unique_years": n_unique_years, "median_obs_per_eligible_series": median_obs,
            "mean_year_coverage_fraction": mean_year_coverage_fraction,
        })
    return pd.DataFrame(rows)


def support_thresholds(study_support: pd.DataFrame) -> dict:
    out = {}
    for k in SERIES_COUNT_THRESHOLDS:
        meeting = study_support[study_support["n_eligible_series"] >= k]
        out[str(k)] = {
            "n_studies": int(meeting.shape[0]),
            "n_series_represented": int(meeting["n_eligible_series"].sum()),
        }
    return out


# =============================================================================
# TASK 4 -- temporal (contemporaneous) overlap audit
# =============================================================================
def contemporaneous_counts(usable: pd.DataFrame, eligible: pd.DataFrame) -> pd.DataFrame:
    """One row per (DataSource_ID, Year): number of ELIGIBLE series with a
    usable observation that year."""
    elig_keys = set(map(tuple, eligible[["DataSource_ID", "Plot_ID", "Stratum"]].values))
    mask = usable.apply(lambda r: (r["DataSource_ID"], r["Plot_ID"], r["Stratum"]) in elig_keys, axis=1)
    elig_usable = usable[mask]
    counts = (
        elig_usable.groupby(["DataSource_ID", "Year"])
        .apply(lambda d: d[["Plot_ID", "Stratum"]].drop_duplicates().shape[0], include_groups=False)
        .reset_index(name="n_contemporaneous_series")
    )
    return counts


def contemporaneous_summary(counts: pd.DataFrame) -> dict:
    c = counts["n_contemporaneous_series"]
    summary = {
        "distribution": {
            "min": int(c.min()), "max": int(c.max()), "mean": float(c.mean()), "median": float(c.median()),
        },
        "study_year_threshold_counts": {},
        "studies_ever_achieving_threshold": {},
        "studies_sustaining_threshold_multiple_years": {},
    }
    for t in CONTEMPORANEOUS_THRESHOLDS:
        meeting = counts[counts["n_contemporaneous_series"] >= t]
        summary["study_year_threshold_counts"][str(t)] = int(meeting.shape[0])
        per_study_years_meeting = meeting.groupby("DataSource_ID").size()
        summary["studies_ever_achieving_threshold"][str(t)] = int(per_study_years_meeting.shape[0])
        summary["studies_sustaining_threshold_multiple_years"][str(t)] = int((per_study_years_meeting >= 2).sum())
    return summary


def consecutive_year_runs(counts: pd.DataFrame, threshold: int) -> dict:
    """For each study, the longest run of consecutive calendar years with
    n_contemporaneous_series >= threshold. Returns per-study max run and
    threshold-count summaries."""
    max_runs = {}
    for ds_id, g in counts.groupby("DataSource_ID"):
        g = g.sort_values("Year")
        meets = g["n_contemporaneous_series"] >= threshold
        years = g["Year"].values
        best, cur, cur_start = 0, 0, None
        prev_year = None
        for y, m in zip(years, meets):
            if m:
                if prev_year is not None and y == prev_year + 1 and cur > 0:
                    cur += 1
                else:
                    cur = 1
                best = max(best, cur)
            else:
                cur = 0
            prev_year = y
        max_runs[ds_id] = best
    runs_series = pd.Series(max_runs)
    return {
        "per_study_max_run": {str(k): int(v) for k, v in max_runs.items()},
        "n_studies_with_run_at_least": {str(r): int((runs_series >= r).sum()) for r in RUN_LENGTH_THRESHOLDS},
    }


# =============================================================================
# TASK 5 -- window feasibility
# =============================================================================
def window_feasibility(usable: pd.DataFrame, eligible: pd.DataFrame) -> dict:
    elig_keys = list(map(tuple, eligible[["DataSource_ID", "Plot_ID", "Stratum"]].values))
    series_years = {k: _series_years(usable, k) for k in elig_keys}
    by_study = {}
    for k in elig_keys:
        by_study.setdefault(k[0], []).append(k)

    results = {}
    for W in WINDOW_LENGTHS:
        nonoverlap_counts, rolling_counts = [], []
        for ds_id, keys in by_study.items():
            all_years = sorted(set(itertools.chain.from_iterable(series_years[k] for k in keys)))
            if not all_years:
                continue
            y0, y1 = min(all_years), max(all_years)

            # non-overlapping (block) windows tiling [y0, y1]
            start = y0
            while start <= y1:
                end = start + W - 1
                n_series_ok = sum(
                    1 for k in keys if sum(1 for y in series_years[k] if start <= y <= end) >= 2
                )
                nonoverlap_counts.append(n_series_ok)
                start += W

            # rolling windows, every possible start year
            for start in range(y0, y1 - W + 2):
                end = start + W - 1
                n_series_ok = sum(
                    1 for k in keys if sum(1 for y in series_years[k] if start <= y <= end) >= 2
                )
                rolling_counts.append(n_series_ok)

        nonoverlap_counts = np.array(nonoverlap_counts) if nonoverlap_counts else np.array([])
        rolling_counts = np.array(rolling_counts) if rolling_counts else np.array([])
        results[str(W)] = {
            "n_nonoverlapping_windows_total": int(len(nonoverlap_counts)),
            "n_rolling_windows_total": int(len(rolling_counts)),
            "nonoverlapping_meeting_threshold": {
                str(t): int((nonoverlap_counts >= t).sum()) for t in WINDOW_SERIES_THRESHOLDS
            },
            "rolling_meeting_threshold": {
                str(t): int((rolling_counts >= t).sum()) for t in WINDOW_SERIES_THRESHOLDS
            },
        }
    return results


# =============================================================================
# TASK 6 -- estimator stability (historical CVs only, real empirical pool)
# =============================================================================
def cv_of_cvs(cvs: np.ndarray):
    cvs = np.asarray(cvs, dtype=float)
    m = cvs.mean()
    if m == 0:
        return None
    return float(cvs.std(ddof=1) / m)


def historical_cv_pool(usable: pd.DataFrame, eligible: pd.DataFrame) -> np.ndarray:
    """Per-eligible-series CV over each series' own full historical
    (usable-year) span -- the same construction as Round 0's
    docs/CV_OF_CV_INTERPRETATION.md, reused, not redefined."""
    cvs = []
    for _, r in eligible.iterrows():
        key = (r["DataSource_ID"], r["Plot_ID"], r["Stratum"])
        sub = usable[
            (usable["DataSource_ID"] == key[0]) & (usable["Plot_ID"] == key[1]) & (usable["Stratum"] == key[2])
        ]
        cv = coefficient_of_variation(sub["Number"].values)
        if cv is not None and np.isfinite(cv):
            cvs.append(cv)
    return np.array(cvs)


def estimator_stability(cv_pool: np.ndarray) -> dict:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    results = {}
    pool_max = float(cv_pool.max())
    for n in GROUP_SIZES:
        if n > len(cv_pool):
            results[str(n)] = {"note": "group size exceeds historical CV pool size, skipped"}
            continue
        estimates, near_zero_denom, undefined = [], 0, 0
        sensitivity_shifts = []
        for _ in range(BOOTSTRAP_RESAMPLES):
            sample = rng.choice(cv_pool, size=n, replace=False)
            est = cv_of_cvs(sample)
            if est is None:
                undefined += 1
                continue
            if sample.mean() < 1e-6:
                near_zero_denom += 1
            estimates.append(est)
            # sensitivity: replace one randomly chosen element with the pool max
            perturbed = sample.copy()
            perturbed[0] = pool_max
            est_perturbed = cv_of_cvs(perturbed)
            if est_perturbed is not None:
                sensitivity_shifts.append(abs(est_perturbed - est))
        estimates = np.array(estimates)
        results[str(n)] = {
            "n_resamples": BOOTSTRAP_RESAMPLES,
            "frequency_undefined": undefined / BOOTSTRAP_RESAMPLES,
            "frequency_near_zero_denominator": near_zero_denom / BOOTSTRAP_RESAMPLES,
            "mean_estimate": float(estimates.mean()) if len(estimates) else None,
            "sd_of_estimate_across_resamples": float(estimates.std(ddof=1)) if len(estimates) > 1 else None,
            "ci_2_5_97_5": [float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))] if len(estimates) else None,
            "ci_width": float(np.quantile(estimates, 0.975) - np.quantile(estimates, 0.025)) if len(estimates) else None,
            "mean_single_extreme_sensitivity_shift": float(np.mean(sensitivity_shifts)) if sensitivity_shifts else None,
        }
    return results


# =============================================================================
# TASK 8 -- LEVEL vs CHANGE feasibility
# =============================================================================
LEVEL_WINDOW = 10          # disclosed default, matches Round 0's own MIN_TOTAL_POINTS convention
LEVEL_MIN_SERIES = 5        # disclosed default, a defensible minimum for an SD estimate


def level_vs_change_feasibility(usable: pd.DataFrame, eligible: pd.DataFrame) -> dict:
    elig_keys = list(map(tuple, eligible[["DataSource_ID", "Plot_ID", "Stratum"]].values))
    series_years = {k: _series_years(usable, k) for k in elig_keys}
    by_study = {}
    for k in elig_keys:
        by_study.setdefault(k[0], []).append(k)

    level_adequate_studies = []
    change_windows_per_study = {}
    for ds_id, keys in by_study.items():
        all_years = sorted(set(itertools.chain.from_iterable(series_years[k] for k in keys)))
        if not all_years:
            continue
        y0, y1 = min(all_years), max(all_years)
        adequate_windows = 0
        start = y0
        while start <= y1:
            end = start + LEVEL_WINDOW - 1
            n_series_ok = sum(1 for k in keys if sum(1 for y in series_years[k] if start <= y <= end) >= 2)
            if n_series_ok >= LEVEL_MIN_SERIES:
                adequate_windows += 1
            start += LEVEL_WINDOW
        change_windows_per_study[ds_id] = adequate_windows
        if adequate_windows >= 1:
            level_adequate_studies.append(ds_id)

    change_counts = pd.Series(change_windows_per_study)
    return {
        "level_window_years": LEVEL_WINDOW, "level_min_series": LEVEL_MIN_SERIES,
        "level_feasibility": {
            "n_studies_with_at_least_one_adequate_window": len(level_adequate_studies),
            "n_studies_total_with_eligible_series": len(by_study),
        },
        "change_feasibility": {
            str(m): int((change_counts >= m).sum()) for m in CHANGE_MIN_WINDOWS
        },
        "change_windows_per_study": {str(k): int(v) for k, v in change_windows_per_study.items()},
    }


# =============================================================================
# TASK 10 -- chronological separation design feasibility (dates/counts only)
# =============================================================================
def chronology_design_feasibility(usable: pd.DataFrame, eligible: pd.DataFrame) -> dict:
    elig_keys = list(map(tuple, eligible[["DataSource_ID", "Plot_ID", "Stratum"]].values))
    series_years = {k: _series_years(usable, k) for k in elig_keys}
    by_study = {}
    for k in elig_keys:
        by_study.setdefault(k[0], []).append(k)

    designs = {}
    for name, frac in [("A_50_50", 0.5), ("B_60_40", 0.6)]:
        n_studies_retained = 0
        future_year_counts = []
        for ds_id, keys in by_study.items():
            all_years = sorted(set(itertools.chain.from_iterable(series_years[k] for k in keys)))
            n = len(all_years)
            if n < 2:
                continue
            n_hist = max(1, round(n * frac))
            hist_years, fut_years = all_years[:n_hist], all_years[n_hist:]
            if not fut_years:
                continue
            n_series_hist_ok = sum(1 for k in keys if sum(1 for y in series_years[k] if y in hist_years) >= 2)
            if n_series_hist_ok >= LEVEL_MIN_SERIES:
                n_studies_retained += 1
                future_year_counts.append(len(fut_years))
        designs[name] = {
            "n_studies_retained": n_studies_retained,
            "median_future_years_available": float(np.median(future_year_counts)) if future_year_counts else None,
            "leakage_risk": "none by construction -- split is by unique-year rank, mirroring "
                            "insect_variance_protocol.chronological_split's own assertion pattern; "
                            "historical portion never reads a future-portion year.",
        }

    # design C: fixed 10-yr history + held-out later period (any remaining years)
    n_studies_c, future_counts_c = 0, []
    for ds_id, keys in by_study.items():
        all_years = sorted(set(itertools.chain.from_iterable(series_years[k] for k in keys)))
        if len(all_years) < LEVEL_WINDOW + 1:
            continue
        hist_years = all_years[:LEVEL_WINDOW]
        fut_years = all_years[LEVEL_WINDOW:]
        n_series_hist_ok = sum(1 for k in keys if sum(1 for y in series_years[k] if y in hist_years) >= 2)
        if n_series_hist_ok >= LEVEL_MIN_SERIES and fut_years:
            n_studies_c += 1
            future_counts_c.append(len(fut_years))
    designs["C_fixed_10yr_history_plus_heldout_later"] = {
        "n_studies_retained": n_studies_c,
        "median_future_years_available": float(np.median(future_counts_c)) if future_counts_c else None,
        "leakage_risk": "none by construction, same rationale as designs A/B.",
    }
    return designs


# =============================================================================
# TASK 11 -- study heterogeneity / confounding audit (structural only)
# =============================================================================
def context_heterogeneity_audit(tables: dict, study_support: pd.DataFrame, contemp_summary_counts: pd.DataFrame) -> pd.DataFrame:
    ds = tables["DataSources"].copy()
    plot = tables["PlotData"]
    samp = tables["SampleData"]

    plots_per_study = plot.groupby("DataSource_ID")["Plot_ID"].nunique().rename("n_plots_in_source")
    methods_per_study = samp.groupby("DataSource_ID")["SamplingMethod"].nunique().rename("n_distinct_sampling_methods")
    treatments_per_study = plot.groupby("DataSource_ID")["ExperimentalTreatment"].apply(
        lambda s: int(s.notna().any())
    ).rename("has_any_treatment_flag")

    # study-year threshold-5 sustained flag from Task 4 output
    achieving5 = set(contemp_summary_counts.loc[contemp_summary_counts["n_contemporaneous_series"] >= 5, "DataSource_ID"].unique())

    merged = study_support.merge(ds[["DataSource_ID", "Realm", "InvertebrateGroup", "AbundanceOrBiomass"]], on="DataSource_ID", how="left")
    merged = merged.merge(plots_per_study, on="DataSource_ID", how="left")
    merged = merged.merge(methods_per_study, on="DataSource_ID", how="left")
    merged = merged.merge(treatments_per_study, on="DataSource_ID", how="left")
    merged["duration_years"] = merged["year_max"] - merged["year_min"]
    merged["meets_contemporaneous_5_threshold_any_year"] = merged["DataSource_ID"].isin(achieving5)
    return merged
