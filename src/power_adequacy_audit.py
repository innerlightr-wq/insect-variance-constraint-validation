#!/usr/bin/env python3
"""
Power / adequacy audit (Task 18). STRICT NO-PEEKING RULE: this script
computes eligibility counts, study/fold structure, and the MARGINAL
distribution of the future-outcome variable (its own distribution, alone)
-- it never computes or inspects any association between a candidate
constraint metric (or any other predictor) and that outcome. No
correlation, no regression, no coefficient, no p-value against the
primary target appears anywhere in this script or its output.

Returns exactly one of READY / UNDERPOWERED / BLOCKED, per the frozen
protocol (docs/HYPOTHESIS_PROTOCOL.md).

Usage:
    python3 src/power_adequacy_audit.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from insect_variance_protocol import (  # noqa: E402
    build_yearly_abundance_table, build_eligibility_table, stratum_adequacy,
    make_group_folds, ols_trend_slope, MIN_TOTAL_POINTS, MIN_WINDOW_POINTS,
    STRATUM_MIN_SERIES, STRATUM_MIN_STUDIES,
)

ENCODING = "latin-1"
DATA_DIR = "data/raw/insect_knb"
N_SPLITS_PRIMARY = 10   # frozen -- see docs/HYPOTHESIS_PROTOCOL.md Task 10
FOLD_MIN_SERIES = 20     # frozen fallback trigger, Task 10


def load_abundance() -> pd.DataFrame:
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding=ENCODING)
    return ab[ab["MetricAB"] == "abundance"].copy()


def marginal_late_trend_for_series(raw_ab: pd.DataFrame, elig_row: pd.Series, yearly: pd.DataFrame) -> float | None:
    key = (elig_row["DataSource_ID"], elig_row["Plot_ID"], elig_row["Stratum"])
    sub = yearly[
        (yearly["DataSource_ID"] == key[0]) & (yearly["Plot_ID"] == key[1]) & (yearly["Stratum"] == key[2])
    ].dropna(subset=["Number"]).sort_values("Year")
    years = sorted(sub["Year"].unique())
    n = len(years)
    n_early = -(-n // 2)  # ceil
    late_years = years[n_early:]
    late = sub[sub["Year"].isin(late_years)]
    return ols_trend_slope(late["Year"].values, np.log1p(late["Number"].values))


def run() -> dict:
    raw_ab = load_abundance()
    yearly = build_yearly_abundance_table(raw_ab)
    eligibility = build_eligibility_table(yearly)
    eligible = eligibility[eligibility["eligible"]].copy()

    n_candidate_series = eligibility.shape[0]
    n_eligible = int(eligible.shape[0])
    n_excluded = n_candidate_series - n_eligible
    exclusion_reasons = eligibility.loc[~eligibility["eligible"], "exclusion_reason"].value_counts().to_dict()

    studies = sorted(eligible["DataSource_ID"].unique())
    n_studies = len(studies)

    # marginal outcome distribution (Y alone, no predictor touched)
    late_trends = eligible.apply(lambda r: marginal_late_trend_for_series(raw_ab, r, yearly), axis=1)
    eligible = eligible.assign(late_trend=late_trends)
    valid_trend = eligible["late_trend"].dropna()

    strat_adeq = stratum_adequacy(eligibility)

    # grouped folds, with the frozen fallback rule applied if needed
    n_splits = N_SPLITS_PRIMARY
    fold_report = None
    while n_splits >= 5:
        folds = make_group_folds(eligible["DataSource_ID"].values, n_splits=n_splits)
        sizes = [len(test_idx) for _, test_idx in folds]
        if min(sizes) >= FOLD_MIN_SERIES:
            fold_report = {"n_splits_used": n_splits, "fold_test_sizes": sizes, "fallback_triggered": n_splits != N_SPLITS_PRIMARY}
            break
        n_splits -= 1
    if fold_report is None:
        fold_report = {"n_splits_used": None, "fold_test_sizes": None, "fallback_triggered": True,
                        "note": f"no n_splits in [5,{N_SPLITS_PRIMARY}] satisfied the >= {FOLD_MIN_SERIES} "
                                f"series-per-fold floor"}

    median_points = float(eligible["n_usable_years"].median()) if n_eligible else None
    median_early = float(eligible["n_early"].median()) if n_eligible else None
    median_late = float(eligible["n_late"].median()) if n_eligible else None

    # --- gate decision (structural only, no outcome-predictor peeking) ---
    reasons = []
    verdict = "READY"
    if n_eligible < 100:
        verdict = "UNDERPOWERED"
        reasons.append(f"only {n_eligible} eligible series (<100)")
    if n_studies < 20:
        verdict = "UNDERPOWERED"
        reasons.append(f"only {n_studies} distinct eligible studies (<20)")
    if fold_report["n_splits_used"] is None:
        verdict = "BLOCKED"
        reasons.append("no valid grouped fold configuration found in [5,10]")
    if not reasons:
        reasons.append(
            f"{n_eligible} eligible series across {n_studies} studies; "
            f"grouped {fold_report['n_splits_used']}-fold validation is feasible "
            f"with a minimum of {min(fold_report['fold_test_sizes'])} series per test fold"
        )

    return {
        "eligibility": {
            "n_candidate_series": int(n_candidate_series),
            "n_eligible": n_eligible,
            "n_excluded": int(n_excluded),
            "exclusion_reasons": exclusion_reasons,
            "min_total_points_rule": MIN_TOTAL_POINTS,
            "min_window_points_rule": MIN_WINDOW_POINTS,
        },
        "studies": {"n_eligible_studies": n_studies},
        "series_length_distribution": {
            "median_usable_years": median_points,
            "median_early_window": median_early,
            "median_late_window": median_late,
            "min_usable_years": int(eligible["n_usable_years"].min()) if n_eligible else None,
            "max_usable_years": int(eligible["n_usable_years"].max()) if n_eligible else None,
        },
        "marginal_future_trend_distribution": {
            "n_with_valid_trend": int(valid_trend.shape[0]),
            "n_undefined": int(eligible.shape[0] - valid_trend.shape[0]),
            "mean": float(valid_trend.mean()) if len(valid_trend) else None,
            "median": float(valid_trend.median()) if len(valid_trend) else None,
            "std": float(valid_trend.std(ddof=1)) if len(valid_trend) > 1 else None,
            "q10": float(valid_trend.quantile(0.10)) if len(valid_trend) else None,
            "q90": float(valid_trend.quantile(0.90)) if len(valid_trend) else None,
            "fraction_negative_slope": float((valid_trend < 0).mean()) if len(valid_trend) else None,
            "note": "MARGINAL distribution of the outcome variable alone -- "
                    "no predictor is referenced anywhere in this computation.",
        },
        "stratum_adequacy_gate": strat_adeq.to_dict(orient="records"),
        "grouped_fold_report": fold_report,
        "gate": {"verdict": verdict, "reasons": reasons},
    }


def write_report(result: dict, out_md: str, out_json: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    e = result["eligibility"]
    sl = result["series_length_distribution"]
    ft = result["marginal_future_trend_distribution"]
    g = result["gate"]

    lines = [
        "# Power / adequacy audit — insect variance-constraint validation (ROUND 0)",
        "",
        "**STRICT NO-PEEKING RULE HELD.** This report contains eligibility "
        "counts, study/fold structure, and the outcome variable's own "
        "marginal distribution only. No candidate constraint metric is "
        "computed, referenced, or compared against the outcome anywhere in "
        "this document. Generated by `src/power_adequacy_audit.py`.",
        "",
        "## Eligibility",
        "",
        f"- Candidate series (DataSource_ID x Plot_ID x Stratum, abundance only): **{e['n_candidate_series']}**",
        f"- Eligible series (>= {e['min_total_points_rule']} usable years, "
        f">= {e['min_window_points_rule']} in each window after the frozen "
        f"chronological split): **{e['n_eligible']}**",
        f"- Excluded: **{e['n_excluded']}**",
        "",
        "| exclusion reason | n |",
        "|---|---:|",
    ]
    for reason, n in e["exclusion_reasons"].items():
        lines.append(f"| {reason} | {n} |")
    lines += [
        "",
        f"- Distinct eligible studies (`DataSource_ID`): **{result['studies']['n_eligible_studies']}**",
        "",
        "## Series-length distribution (eligible series only)",
        "",
        f"- median usable years: {sl['median_usable_years']}",
        f"- median early-window points: {sl['median_early_window']}",
        f"- median late-window points: {sl['median_late_window']}",
        f"- range: [{sl['min_usable_years']}, {sl['max_usable_years']}]",
        "",
        "## Marginal distribution of the future outcome (Y alone — no predictor referenced)",
        "",
        f"- series with a defined late-window trend: {ft['n_with_valid_trend']} "
        f"({ft['n_undefined']} undefined — late window had <2 distinct years, "
        "should not occur under the frozen eligibility rule, reported for "
        "transparency)",
        f"- mean: {ft['mean']:.5f}" if ft["mean"] is not None else "- mean: n/a",
        f"- median: {ft['median']:.5f}" if ft["median"] is not None else "- median: n/a",
        f"- std: {ft['std']:.5f}" if ft["std"] is not None else "- std: n/a",
        f"- 10th/90th percentile: [{ft['q10']:.5f}, {ft['q90']:.5f}]" if ft["q10"] is not None else "",
        f"- fraction with negative slope (declining): {ft['fraction_negative_slope']:.1%}" if ft["fraction_negative_slope"] is not None else "",
        "",
        "## Stratum adequacy gate (Task 14: >= 30 series AND >= 5 studies)",
        "",
        "| stratum | n_series | n_studies | adequate for H3 |",
        "|---|---:|---:|---|",
    ]
    for row in result["stratum_adequacy_gate"]:
        lines.append(f"| {row['Stratum']} | {row['n_series']} | {row['n_studies']} | {row['adequate_for_H3']} |")

    fr = result["grouped_fold_report"]
    lines += [
        "",
        "## Grouped (study-aware) fold report",
        "",
        f"- folds used: {fr['n_splits_used']}",
        f"- fallback triggered: {fr['fallback_triggered']}",
        f"- test-fold sizes: {fr['fold_test_sizes']}",
        "",
        "## Gate decision",
        "",
        f"# **{g['verdict']}**",
        "",
    ]
    for r in g["reasons"]:
        lines.append(f"- {r}")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    result = run()
    write_report(result, "results/POWER_ADEQUACY_AUDIT.md", "results/power_adequacy_audit.json")
    print("verdict:", result["gate"]["verdict"])
    print("wrote results/POWER_ADEQUACY_AUDIT.md and results/power_adequacy_audit.json")


if __name__ == "__main__":
    main()
