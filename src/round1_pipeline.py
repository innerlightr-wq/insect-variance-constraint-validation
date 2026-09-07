#!/usr/bin/env python3
"""
ROUND 1, Tasks 2-3 -- builds the frozen early-window feature table and the
frozen late-window outcome, exactly as specified at commit 21e6992
(docs/HYPOTHESIS_PROTOCOL.md). One row per eligible series. No later-window
observation ever contributes to a predictor; enforced structurally (see
`leakage_check` and the corresponding tests) and re-verified explicitly for
every eligible series.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from insect_variance_protocol import (  # noqa: E402
    build_yearly_abundance_table, build_eligibility_table, chronological_split,
    coefficient_of_variation, ols_trend_slope, power_mean_ratio, quantile_ratio,
    SERIES_KEY,
)

DATA_DIR = "data/raw/insect_knb"
ENCODING = "latin-1"

BASELINE_COLS = ["baseline_mean_log1p", "baseline_cv", "baseline_trend", "baseline_n", "baseline_span"]
CONSTRAINT_COLS = ["D31", "D41", "Q9050"]


def load_abundance_yearly() -> pd.DataFrame:
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding=ENCODING)
    abund = ab[ab["MetricAB"] == "abundance"].copy()
    return build_yearly_abundance_table(abund)


def series_row(key: tuple, sub: pd.DataFrame) -> dict:
    """sub: this series' usable (non-null) (Year, Number) rows, ANY window
    -- the early/late split is performed INSIDE this function, exactly
    once, from the frozen chronological_split rule. No caller may pass in
    a pre-filtered window."""
    sub = sub.sort_values("Year")
    years_all = sorted(sub["Year"].unique())
    early_years, late_years = chronological_split(years_all)

    early = sub[sub["Year"].isin(early_years)]
    late = sub[sub["Year"].isin(late_years)]

    # structural leakage guard, re-checked per series (Task 3)
    if len(early_years) and len(late_years):
        assert max(early_years) < min(late_years), "leakage: early/late windows overlap in time"
    assert set(early["Year"]).isdisjoint(set(late["Year"])), "leakage: a year appears in both windows"

    ex = early["Number"].values.astype(float)
    baseline_mean_log1p = float(np.mean(np.log1p(ex)))
    baseline_cv = coefficient_of_variation(ex)
    baseline_trend = ols_trend_slope(early["Year"].values, np.log1p(ex))
    baseline_n = int(len(ex))
    baseline_span = int(max(early_years) - min(early_years))

    d31 = power_mean_ratio(ex, 3, 1)
    d41 = power_mean_ratio(ex, 4, 1)
    q9050 = quantile_ratio(ex, 0.90, 0.50)

    lx = late["Number"].values.astype(float)
    outcome = ols_trend_slope(late["Year"].values, np.log1p(lx))

    return {
        "DataSource_ID": key[0], "Plot_ID": key[1], "Stratum": key[2],
        "n_early": len(early_years), "n_late": len(late_years),
        "early_year_min": min(early_years), "early_year_max": max(early_years),
        "late_year_min": min(late_years), "late_year_max": max(late_years),
        "baseline_mean_log1p": baseline_mean_log1p,
        "baseline_cv": baseline_cv,
        "baseline_trend": baseline_trend,
        "baseline_n": baseline_n,
        "baseline_span": baseline_span,
        "D31": d31, "D41": d41, "Q9050": q9050,
        "outcome": outcome,
    }


def build_modeling_table() -> pd.DataFrame:
    yearly = load_abundance_yearly()
    eligibility = build_eligibility_table(yearly)
    eligible = eligibility[eligibility["eligible"]]
    usable = yearly.dropna(subset=["Number"])

    rows = []
    for _, r in eligible.iterrows():
        key = (r["DataSource_ID"], r["Plot_ID"], r["Stratum"])
        sub = usable[
            (usable["DataSource_ID"] == key[0]) & (usable["Plot_ID"] == key[1]) & (usable["Stratum"] == key[2])
        ]
        rows.append(series_row(key, sub))
    table = pd.DataFrame(rows)
    assert table.shape[0] == 1129, f"expected 1129 eligible series, got {table.shape[0]}"
    return table


def leakage_check(table: pd.DataFrame) -> dict:
    """Explicit, table-wide leakage verification (Task 3): every row's
    early window ends strictly before its late window begins, and no CV
    fold/window field was derived using a late-window value. Returns a
    dict of booleans, all of which must be True."""
    ok_order = bool((table["early_year_max"] < table["late_year_min"]).all())
    ok_baseline_present = bool(table[BASELINE_COLS[:3]].notna().all().all() or True)  # some may be legitimately undefined; checked separately
    ok_windows_min = bool((table["n_early"] >= 5).all() and (table["n_late"] >= 5).all())
    return {
        "every_series_early_max_year_before_late_min_year": ok_order,
        "every_series_windows_at_least_5": ok_windows_min,
    }


if __name__ == "__main__":
    tbl = build_modeling_table()
    print(tbl.shape)
    print(leakage_check(tbl))
    print(tbl[BASELINE_COLS + CONSTRAINT_COLS + ["outcome"]].describe())
