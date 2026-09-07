"""
Tests for src/insect_variance_protocol.py. ROUND 0 -- these tests verify
the pure mathematical/logical primitives (power means, scale invariance,
chronological split, eligibility, grouped folds, permutation controls,
checksum validation) against synthetic data with known answers. They do
NOT compute, and never assert on, any association between a constraint
metric and the real corpus's future outcome.
"""
import hashlib
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import insect_variance_protocol as ivp  # noqa: E402


# --------------------------------------------------------------------------- power mean
def test_power_mean_p1_is_arithmetic_mean():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert abs(ivp.power_mean(x, 1) - x.mean()) < 1e-12


def test_power_mean_constant_series_equals_the_constant_at_any_p():
    x = np.array([5.0, 5.0, 5.0])
    for p in (1, 2, 3, 4):
        assert abs(ivp.power_mean(x, p) - 5.0) < 1e-9


def test_power_mean_rejects_negative_values():
    with pytest.raises(ValueError):
        ivp.power_mean(np.array([1.0, -1.0]), 3)


def test_power_mean_rejects_empty():
    with pytest.raises(ValueError):
        ivp.power_mean(np.array([]), 3)


def test_power_mean_ordering_M3_at_least_M1_for_nonconstant():
    rng = np.random.default_rng(0)
    x = rng.exponential(size=50) + 0.01
    assert ivp.power_mean(x, 3) >= ivp.power_mean(x, 1) - 1e-9


# --------------------------------------------------------------------------- CV
def test_cv_zero_for_constant_series():
    x = np.array([3.0, 3.0, 3.0, 3.0])
    assert abs(ivp.coefficient_of_variation(x)) < 1e-12


def test_cv_undefined_for_zero_mean():
    x = np.array([-1.0, 1.0])  # not realistic for abundance but tests the guard
    assert ivp.coefficient_of_variation(x) is None


def test_cv_undefined_for_single_point():
    assert ivp.coefficient_of_variation(np.array([5.0])) is None


# --------------------------------------------------------------------------- power_mean_ratio / D_p1
def test_power_mean_ratio_equals_one_for_constant_series():
    x = np.array([7.0] * 10)
    assert abs(ivp.power_mean_ratio(x, 3, 1) - 1.0) < 1e-9
    assert abs(ivp.power_mean_ratio(x, 4, 1) - 1.0) < 1e-9


def test_power_mean_ratio_at_least_one_for_nonconstant():
    rng = np.random.default_rng(1)
    x = rng.exponential(size=100) + 0.01
    assert ivp.power_mean_ratio(x, 3, 1) >= 1.0 - 1e-9
    assert ivp.power_mean_ratio(x, 4, 1) >= 1.0 - 1e-9


def test_power_mean_ratio_undefined_when_all_zero():
    x = np.zeros(5)
    assert ivp.power_mean_ratio(x, 3, 1) is None


def test_power_mean_ratio_scale_invariance():
    rng = np.random.default_rng(2)
    x = rng.exponential(size=30) + 0.01
    base = ivp.power_mean_ratio(x, 3, 1)
    for c in (0.001, 0.5, 1.0, 2.0, 100.0, 1e6):
        scaled = ivp.power_mean_ratio(c * x, 3, 1)
        assert abs(scaled - base) < 1e-8, f"D_3/1 not scale invariant at c={c}"
    base4 = ivp.power_mean_ratio(x, 4, 1)
    for c in (0.5, 3.0, 1000.0):
        scaled4 = ivp.power_mean_ratio(c * x, 4, 1)
        assert abs(scaled4 - base4) < 1e-7, f"D_4/1 not scale invariant at c={c}"


# --------------------------------------------------------------------------- quantile ratio
def test_quantile_ratio_equals_one_for_constant_series():
    x = np.array([2.0] * 20)
    assert abs(ivp.quantile_ratio(x) - 1.0) < 1e-12


def test_quantile_ratio_scale_invariance():
    rng = np.random.default_rng(3)
    x = rng.exponential(size=50) + 0.01
    base = ivp.quantile_ratio(x)
    for c in (0.01, 2.0, 500.0):
        assert abs(ivp.quantile_ratio(c * x) - base) < 1e-8


def test_quantile_ratio_undefined_when_median_zero():
    x = np.array([0, 0, 0, 1, 2])  # median = 0
    assert ivp.quantile_ratio(x) is None


# --------------------------------------------------------------------------- OLS trend slope
def test_ols_trend_slope_recovers_exact_linear_trend():
    years = np.arange(2000, 2010)
    values = 3.0 + 0.5 * (years - 2000)
    slope = ivp.ols_trend_slope(years, values)
    assert abs(slope - 0.5) < 1e-9


def test_ols_trend_slope_negative_for_decline():
    years = np.arange(2000, 2010)
    values = 10.0 - 0.2 * (years - 2000)
    assert ivp.ols_trend_slope(years, values) < 0


def test_ols_trend_slope_none_for_single_year():
    assert ivp.ols_trend_slope(np.array([2000, 2000]), np.array([1.0, 2.0])) is None


# --------------------------------------------------------------------------- chronological split / no leakage
def test_chronological_split_10_years_gives_5_and_5():
    years = list(range(2000, 2010))
    early, late = ivp.chronological_split(years)
    assert len(early) == 5 and len(late) == 5
    assert early == list(range(2000, 2005))
    assert late == list(range(2005, 2010))


def test_chronological_split_odd_length_favors_early_with_ceil():
    years = list(range(2000, 2011))  # 11 years
    early, late = ivp.chronological_split(years)
    assert len(early) == 6 and len(late) == 5


def test_chronological_split_no_leakage_boundary():
    years = [2001, 2005, 2003, 2007, 2009, 2002, 2008, 2004, 2006, 2000]
    early, late = ivp.chronological_split(years)
    assert max(early) < min(late)


def test_chronological_split_deduplicates_years():
    years = [2000, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2008]
    early, late = ivp.chronological_split(years)
    assert len(early) + len(late) == 9  # 9 distinct years, not 11 raw entries


# --------------------------------------------------------------------------- duplicate-year / missing-value handling
def test_aggregate_within_year_sums_multiple_periods():
    df = pd.DataFrame({
        "DataSource_ID": [1, 1, 1], "Plot_ID": [10, 10, 10], "Stratum": ["Air"] * 3,
        "Year": [2000, 2000, 2001], "Number": [4.0, 6.0, 5.0],
    })
    out = ivp.aggregate_within_year(df)
    row2000 = out[out["Year"] == 2000].iloc[0]
    assert row2000["Number"] == 10.0
    row2001 = out[out["Year"] == 2001].iloc[0]
    assert row2001["Number"] == 5.0


def test_aggregate_within_year_all_null_stays_null_not_zero():
    df = pd.DataFrame({
        "DataSource_ID": [1, 1], "Plot_ID": [10, 10], "Stratum": ["Air", "Air"],
        "Year": [2000, 2000], "Number": [np.nan, np.nan],
    })
    out = ivp.aggregate_within_year(df)
    assert pd.isna(out.iloc[0]["Number"]), "an all-null year must remain null, never become 0"


def test_aggregate_within_year_partial_null_sums_the_observed_value():
    df = pd.DataFrame({
        "DataSource_ID": [1, 1], "Plot_ID": [10, 10], "Stratum": ["Air", "Air"],
        "Year": [2000, 2000], "Number": [np.nan, 7.0],
    })
    out = ivp.aggregate_within_year(df)
    assert out.iloc[0]["Number"] == 7.0


# --------------------------------------------------------------------------- eligibility logic
def test_eligibility_for_series_below_minimum_excluded():
    years = pd.Series(list(range(2000, 2007)))  # 7 years, below MIN_TOTAL_POINTS=10
    elig = ivp.eligibility_for_series(years)
    assert elig.eligible is False
    assert "fewer than" in elig.exclusion_reason


def test_eligibility_for_series_at_minimum_included():
    years = pd.Series(list(range(2000, 2010)))  # exactly 10 years
    elig = ivp.eligibility_for_series(years)
    assert elig.eligible is True
    assert len(elig.early_years) >= ivp.MIN_WINDOW_POINTS
    assert len(elig.late_years) >= ivp.MIN_WINDOW_POINTS


def test_build_eligibility_table_end_to_end_synthetic():
    rows = []
    # series X: 12 usable years -> eligible
    for y in range(2000, 2012):
        rows.append({"DataSource_ID": 1, "Plot_ID": 1, "Stratum": "Air", "Year": y, "Number": 10.0})
    # series Y: 5 usable years -> not eligible
    for y in range(2000, 2005):
        rows.append({"DataSource_ID": 1, "Plot_ID": 2, "Stratum": "Air", "Year": y, "Number": 3.0})
    # series Z: 10 years but all null -> zero usable years
    for y in range(2000, 2010):
        rows.append({"DataSource_ID": 2, "Plot_ID": 3, "Stratum": "Water", "Year": y, "Number": np.nan})
    yearly = pd.DataFrame(rows)
    table = ivp.build_eligibility_table(yearly)
    assert table.shape[0] == 3
    elig_map = {(r.DataSource_ID, r.Plot_ID, r.Stratum): r.eligible for r in table.itertuples()}
    assert elig_map[(1, 1, "Air")] is True
    assert elig_map[(1, 2, "Air")] is False
    assert elig_map[(2, 3, "Water")] is False
    z_row = table[(table.Plot_ID == 3)].iloc[0]
    assert "zero usable years" in z_row["exclusion_reason"]


# --------------------------------------------------------------------------- stratum adequacy gate
def test_stratum_adequacy_gate_thresholds():
    table = pd.DataFrame([
        {"DataSource_ID": s, "Plot_ID": p, "Stratum": "Air", "eligible": True}
        for s in range(5) for p in range(10)  # 5 studies, 50 series -> adequate
    ] + [
        {"DataSource_ID": s, "Plot_ID": p, "Stratum": "Water", "eligible": True}
        for s in range(2) for p in range(40)  # 2 studies (< 5), 80 series -> not adequate (studies)
    ])
    result = ivp.stratum_adequacy(table).set_index("Stratum")
    assert result.loc["Air", "adequate_for_H3"] == True  # noqa: E712
    assert result.loc["Water", "adequate_for_H3"] == False  # noqa: E712


# --------------------------------------------------------------------------- grouped folds
def test_make_group_folds_keeps_study_together():
    groups = np.array([1, 1, 1, 2, 2, 3, 3, 3, 4, 4])
    folds = ivp.make_group_folds(groups, n_splits=4)
    assert len(folds) == 4
    for _, test_idx in folds:
        test_groups = set(groups[test_idx])
        # a study's rows must never be split: check no other fold's test set
        # contains any of the same group ids
        for _, other_test_idx in folds:
            if list(other_test_idx) == list(test_idx):
                continue
            assert test_groups.isdisjoint(set(groups[other_test_idx]))


def test_make_group_folds_deterministic():
    groups = np.array([1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
    folds_a = ivp.make_group_folds(groups, n_splits=5, seed=42)
    folds_b = ivp.make_group_folds(groups, n_splits=5, seed=42)
    for (_, test_a), (_, test_b) in zip(folds_a, folds_b):
        assert list(test_a) == list(test_b)


# --------------------------------------------------------------------------- negative-control permutation logic
def test_permute_within_group_preserves_group_multiset():
    values = np.array([1, 2, 3, 4, 5, 6])
    groups = np.array(["a", "a", "a", "b", "b", "b"])
    permuted = ivp.permute_within_group(values, groups, seed=0)
    assert sorted(permuted[groups == "a"]) == [1, 2, 3]
    assert sorted(permuted[groups == "b"]) == [4, 5, 6]


def test_permute_within_group_singleton_group_unchanged():
    values = np.array([10, 20, 30])
    groups = np.array(["a", "b", "b"])
    permuted = ivp.permute_within_group(values, groups, seed=1)
    assert permuted[0] == 10  # group "a" has only one member -- cannot change


def test_permute_within_group_deterministic_seed():
    values = np.arange(20)
    groups = np.array([i % 4 for i in range(20)])
    p1 = ivp.permute_within_group(values, groups, seed=99)
    p2 = ivp.permute_within_group(values, groups, seed=99)
    assert list(p1) == list(p2)


def test_permute_within_group_different_seed_can_differ():
    values = np.arange(50)
    groups = np.zeros(50, dtype=int)  # one big group so a permutation is possible
    p1 = ivp.permute_within_group(values, groups, seed=1)
    p2 = ivp.permute_within_group(values, groups, seed=2)
    assert list(p1) != list(p2)


def test_time_reversal_pseudo_future_swaps_windows():
    early = np.array([1.0, 2.0, 3.0])
    late = np.array([9.0, 8.0, 7.0])
    swapped_pred, swapped_outcome = ivp.time_reversal_pseudo_future(early, late)
    assert list(swapped_pred) == list(late)
    assert list(swapped_outcome) == list(early)


# --------------------------------------------------------------------------- checksum validation
def test_sha256_and_md5_and_verify_checksum(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("insect variance constraint validation")
    expected_md5 = hashlib.md5(p.read_bytes()).hexdigest()
    expected_sha256 = hashlib.sha256(p.read_bytes()).hexdigest()
    assert ivp.md5_of_file(str(p)) == expected_md5
    assert ivp.sha256_of_file(str(p)) == expected_sha256
    assert ivp.verify_checksum(str(p), expected_md5) is True
    assert ivp.verify_checksum(str(p), "0" * 32) is False


# --------------------------------------------------------------------------- log1p transform behavior (Task 8)
def test_log1p_defined_at_zero_unlike_log():
    assert np.log1p(0.0) == 0.0
    with np.errstate(divide="ignore"):
        assert np.isneginf(np.log(0.0))
