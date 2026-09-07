"""
Tests for src/round2a_cv_of_cv_feasibility.py and
src/round2a_no_peeking_audit.py. Real-data tests are skipped if the corpus
has not been fetched locally. Synthetic tests never touch the real corpus
or any outcome value.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
DATA_DIR = os.path.join(ROOT, "data", "raw", "insect_knb")

skip_no_data = pytest.mark.skipif(
    not os.path.exists(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv")),
    reason="data/raw/insect_knb/ not present locally -- see data/README.md to fetch it",
)


# --------------------------------------------------------------------------- CV-of-CVs primitive
def test_cv_of_cvs_basic():
    import round2a_cv_of_cv_feasibility as r2
    cvs = np.array([0.5, 0.5, 0.5])
    assert abs(r2.cv_of_cvs(cvs)) < 1e-12  # constant CVs -> zero dispersion


def test_cv_of_cvs_undefined_when_mean_zero():
    import round2a_cv_of_cv_feasibility as r2
    assert r2.cv_of_cvs(np.array([0.0, 0.0, 0.0])) is None


def test_cv_of_cvs_matches_manual_computation():
    import round2a_cv_of_cv_feasibility as r2
    cvs = np.array([0.2, 0.4, 0.6, 0.8])
    expected = cvs.std(ddof=1) / cvs.mean()
    assert abs(r2.cv_of_cvs(cvs) - expected) < 1e-12


def test_cv_of_cvs_scale_invariance():
    """CV_of_CVs is built from per-series CVs, each already scale-invariant
    (docs/METRIC_PROPERTIES.md) -- scaling the underlying CV values
    themselves (not raw abundance) should NOT be expected invariant, since
    CV_of_CVs measures dispersion OF the CV values, not of abundance. This
    test instead verifies the correct, actually-claimed invariance: CV
    itself is scale-invariant to raw-abundance rescaling."""
    from insect_variance_protocol import coefficient_of_variation
    rng = np.random.default_rng(0)
    x = rng.exponential(size=30) + 0.1
    base = coefficient_of_variation(x)
    for c in (0.01, 5.0, 1000.0):
        assert abs(coefficient_of_variation(c * x) - base) < 1e-8


# --------------------------------------------------------------------------- contemporaneous counting
def test_contemporaneous_counts_basic():
    import round2a_cv_of_cv_feasibility as r2
    usable = pd.DataFrame({
        "DataSource_ID": [1, 1, 1, 1, 2],
        "Plot_ID": [10, 10, 11, 11, 20],
        "Stratum": ["Air"] * 4 + ["Water"],
        "Year": [2000, 2001, 2000, 2001, 2000],
        "Number": [5.0, 6.0, 7.0, 8.0, 1.0],
    })
    eligible = pd.DataFrame({
        "DataSource_ID": [1, 1, 2], "Plot_ID": [10, 11, 20], "Stratum": ["Air", "Air", "Water"],
    })
    counts = r2.contemporaneous_counts(usable, eligible)
    row_2000_study1 = counts[(counts.DataSource_ID == 1) & (counts.Year == 2000)].iloc[0]
    assert row_2000_study1["n_contemporaneous_series"] == 2  # two series (plots 10, 11) present in 2000
    row_2000_study2 = counts[(counts.DataSource_ID == 2) & (counts.Year == 2000)].iloc[0]
    assert row_2000_study2["n_contemporaneous_series"] == 1


def test_contemporaneous_counts_excludes_ineligible_series():
    import round2a_cv_of_cv_feasibility as r2
    usable = pd.DataFrame({
        "DataSource_ID": [1, 1], "Plot_ID": [10, 11], "Stratum": ["Air", "Air"],
        "Year": [2000, 2000], "Number": [5.0, 6.0],
    })
    eligible = pd.DataFrame({"DataSource_ID": [1], "Plot_ID": [10], "Stratum": ["Air"]})  # plot 11 not eligible
    counts = r2.contemporaneous_counts(usable, eligible)
    assert counts.iloc[0]["n_contemporaneous_series"] == 1


# --------------------------------------------------------------------------- consecutive-year runs
def test_consecutive_year_runs_finds_longest_run():
    import round2a_cv_of_cv_feasibility as r2
    counts = pd.DataFrame({
        "DataSource_ID": [1] * 6,
        "Year": [2000, 2001, 2002, 2004, 2005, 2006],
        "n_contemporaneous_series": [5, 5, 5, 5, 5, 5],
    })
    result = r2.consecutive_year_runs(counts, threshold=5)
    assert result["per_study_max_run"]["1"] == 3  # 2000-2002 and 2004-2006 are each length-3 runs


def test_consecutive_year_runs_below_threshold_breaks_run():
    import round2a_cv_of_cv_feasibility as r2
    counts = pd.DataFrame({
        "DataSource_ID": [1] * 4,
        "Year": [2000, 2001, 2002, 2003],
        "n_contemporaneous_series": [5, 5, 2, 5],  # dips below threshold at 2002
    })
    result = r2.consecutive_year_runs(counts, threshold=5)
    assert result["per_study_max_run"]["1"] == 2


# --------------------------------------------------------------------------- window construction (rolling / non-overlapping)
def test_window_feasibility_counts_are_consistent_synthetic():
    import round2a_cv_of_cv_feasibility as r2
    # 2 series in one study, each with 6 usable years spanning 2000-2005
    usable = pd.DataFrame({
        "DataSource_ID": [1] * 12,
        "Plot_ID": [10] * 6 + [11] * 6,
        "Stratum": ["Air"] * 12,
        "Year": list(range(2000, 2006)) * 2,
        "Number": list(range(1, 7)) * 2,
    })
    eligible = pd.DataFrame({"DataSource_ID": [1, 1], "Plot_ID": [10, 11], "Stratum": ["Air", "Air"]})
    result = r2.window_feasibility(usable, eligible)
    w3 = result["3"]
    assert w3["n_nonoverlapping_windows_total"] == 2  # [2000-2002], [2003-2005]
    # rolling 3-yr windows over a 6-year span: starts 2000,2001,2002,2003 -> 4 windows
    assert w3["n_rolling_windows_total"] == 4
    # both series present with >=2 obs in every window -> all windows meet threshold=2
    assert w3["nonoverlapping_meeting_threshold"]["3"] == 0  # only 2 series total, can't meet a 3-series bar


# --------------------------------------------------------------------------- minimum-series threshold enforcement
def test_support_thresholds_enforced():
    import round2a_cv_of_cv_feasibility as r2
    study_support = pd.DataFrame({
        "DataSource_ID": [1, 2, 3], "n_eligible_series": [2, 6, 12],
    })
    result = r2.support_thresholds(study_support)
    assert result["2"]["n_studies"] == 3
    assert result["5"]["n_studies"] == 2
    assert result["10"]["n_studies"] == 1


# --------------------------------------------------------------------------- study-level grouping
def test_study_multiseries_support_groups_by_study():
    import round2a_cv_of_cv_feasibility as r2
    usable = pd.DataFrame({
        "DataSource_ID": [1, 1, 2], "Plot_ID": [10, 11, 20], "Stratum": ["Air"] * 3,
        "Year": [2000, 2000, 2000], "Number": [5.0, 6.0, 1.0],
    })
    eligibility = pd.DataFrame({
        "DataSource_ID": [1, 1, 2], "Plot_ID": [10, 11, 20], "Stratum": ["Air"] * 3,
        "eligible": [True, True, False],
    })
    result = r2.study_multiseries_support(usable, eligibility)
    row1 = result[result.DataSource_ID == 1].iloc[0]
    assert row1["n_eligible_series"] == 2
    row2 = result[result.DataSource_ID == 2].iloc[0]
    assert row2["n_eligible_series"] == 0


# --------------------------------------------------------------------------- no-peeking guard (Task 12, enforced going forward)
def test_no_peeking_guard():
    import round2a_no_peeking_audit as npa
    result = npa.run()
    assert result["NO_PEEKING_CONFIRMED"] is True, result["forbidden_pattern_hits"]


# --------------------------------------------------------------------------- deterministic bootstrap seed
def test_estimator_stability_deterministic_with_fixed_seed():
    import round2a_cv_of_cv_feasibility as r2
    pool = np.array([0.3, 0.5, 0.7, 0.9, 1.1, 0.4, 0.6, 0.8, 1.0, 0.2, 0.35, 0.55])
    old_resamples = r2.BOOTSTRAP_RESAMPLES
    r2.BOOTSTRAP_RESAMPLES = 50  # small override for test speed
    try:
        result_a = r2.estimator_stability(pool)
        result_b = r2.estimator_stability(pool)
    finally:
        r2.BOOTSTRAP_RESAMPLES = old_resamples
    assert result_a["3"]["mean_estimate"] == result_b["3"]["mean_estimate"]
    assert result_a["5"]["ci_width"] == result_b["5"]["ci_width"]


# --------------------------------------------------------------------------- real-data smoke tests
@skip_no_data
def test_real_data_study_support_matches_documented_numbers():
    import round2a_cv_of_cv_feasibility as r2
    usable, eligibility, eligible = r2.load_usable_and_eligibility()
    study_support = r2.study_multiseries_support(usable, eligibility)
    thresholds = r2.support_thresholds(study_support)
    assert int((study_support["n_eligible_series"] > 0).sum()) == 99
    assert thresholds["5"]["n_studies"] == 38
    assert thresholds["30"]["n_studies"] == 10


@skip_no_data
def test_real_data_level_vs_change_matches_documented_numbers():
    import round2a_cv_of_cv_feasibility as r2
    usable, eligibility, eligible = r2.load_usable_and_eligibility()
    lc = r2.level_vs_change_feasibility(usable, eligible)
    assert lc["level_feasibility"]["n_studies_with_at_least_one_adequate_window"] == 38
    assert lc["change_feasibility"]["3"] == 14
    assert lc["change_feasibility"]["5"] == 3
