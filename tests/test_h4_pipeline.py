"""
Tests for src/h4_pipeline.py -- the frozen H4 implementation skeleton.

ALL tests here use SYNTHETIC fixtures only. No real corpus data, no real
Round 1 outcome value, and no real H4 statistic is loaded or computed
anywhere in this file, per docs/H4_PROTOCOL.md's own STOP rule and
Task 18/19's explicit instruction. This is enforced structurally: none of
these tests import data/raw/insect_knb, and there is no skip-if-data-
present guard anywhere in this file (unlike other test files in this
project) precisely because nothing here should ever need the real corpus.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import h4_pipeline as h4  # noqa: E402


def _synthetic_usable(rows):
    return pd.DataFrame(rows, columns=["DataSource_ID", "Plot_ID", "Stratum", "Year", "Number"])


# --------------------------------------------------------------------------- >=15 threshold
def test_min_constituent_series_is_15():
    assert h4.MIN_CONSTITUENT_SERIES == 15


def test_study_h4_adequate_fails_below_15_constituents():
    rows = []
    for plot in range(14):  # only 14 series -- one short of the frozen minimum
        for y in range(2000, 2012):  # 12 years -> 10-year window + 2 future years, window itself is not the limiting factor
            rows.append([1, plot, "Air", y, 10.0 + plot])
    usable = _synthetic_usable(rows)
    keys = [(1, p, "Air") for p in range(14)]
    result = h4.study_h4_adequate(usable, keys, 1)
    assert result["adequate"] is False
    assert "constituent series" in result["reason"]


def test_study_h4_adequate_passes_at_exactly_15_constituents():
    rows = []
    for plot in range(15):
        for y in range(2000, 2012):  # 12 years total, 10 in window + 2 future
            rows.append([1, plot, "Air", y, 10.0 + plot + (y % 3)])
    usable = _synthetic_usable(rows)
    keys = [(1, p, "Air") for p in range(15)]
    result = h4.study_h4_adequate(usable, keys, 1)
    assert result["adequate"] is True
    assert len(result["constituent_keys"]) == 15


# --------------------------------------------------------------------------- exactly 10-year historical window
def test_historical_window_uses_exactly_10_union_years():
    rows = [[1, 0, "Air", y, 5.0] for y in range(2000, 2015)]  # 15 years
    usable = _synthetic_usable(rows)
    keys = [(1, 0, "Air")]
    window = h4.h4_historical_window(usable, keys, 1)
    assert window["hist_years"] == list(range(2000, 2010))
    assert window["fut_years"] == list(range(2010, 2015))


def test_historical_window_is_rank_based_not_calendar_arithmetic():
    """A gap year with zero coverage should not count toward the 10-year window."""
    years_present = [2000, 2001, 2002, 2003, 2004, 2007, 2008, 2009, 2010, 2011, 2012]  # gap 2005-2006
    rows = [[1, 0, "Air", y, 5.0] for y in years_present]
    usable = _synthetic_usable(rows)
    keys = [(1, 0, "Air")]
    window = h4.h4_historical_window(usable, keys, 1)
    assert window["hist_years"] == years_present[:10]
    assert window["hist_years"][-1] == 2011  # the 10th UNION year, not calendar year 2009


def test_historical_window_none_if_insufficient_years():
    rows = [[1, 0, "Air", y, 5.0] for y in range(2000, 2010)]  # exactly 10 years, no future left
    usable = _synthetic_usable(rows)
    keys = [(1, 0, "Air")]
    assert h4.h4_historical_window(usable, keys, 1) is None


# --------------------------------------------------------------------------- Design-C chronology / no future leakage
def test_no_future_leakage_assertion_holds():
    rows = [[1, 0, "Air", y, 5.0] for y in range(1990, 2020)]
    usable = _synthetic_usable(rows)
    keys = [(1, 0, "Air")]
    window = h4.h4_historical_window(usable, keys, 1)
    assert max(window["hist_years"]) < min(window["fut_years"])


def test_compute_C_g_never_reads_future_values():
    """Construct a study where future-period abundance is wildly different
    from historical -- C_g must be identical regardless of what the future
    values are, proving no future value leaks into C_g."""
    rows = []
    for plot in range(16):
        for y in range(2000, 2010):
            rows.append([1, plot, "Air", y, 10.0 + plot])  # historical: modest values
    keys = [(1, p, "Air") for p in range(16)]
    window = {"hist_years": list(range(2000, 2010))}

    usable_a = _synthetic_usable(rows + [[1, 0, "Air", 2010, 1.0]])       # future = tiny
    usable_b = _synthetic_usable(rows + [[1, 0, "Air", 2010, 999999.0]])  # future = huge

    constituents = h4.constituent_series_for_window(usable_a, keys, 1, window["hist_years"])
    cg_a = h4.compute_C_g(usable_a, constituents, window["hist_years"])
    cg_b = h4.compute_C_g(usable_b, constituents, window["hist_years"])
    assert cg_a == cg_b


# --------------------------------------------------------------------------- outcome eligibility filter
def test_series_outcome_eligible_true_when_strictly_after_cutoff():
    assert h4.series_outcome_eligible(2015, [2000, 2001, 2009]) is True


def test_series_outcome_eligible_false_when_overlapping_or_before():
    assert h4.series_outcome_eligible(2005, [2000, 2001, 2009]) is False
    assert h4.series_outcome_eligible(2009, [2000, 2001, 2009]) is False


# --------------------------------------------------------------------------- CV / CV-of-CVs
def test_cv_and_cv_of_cvs_synthetic():
    from insect_variance_protocol import coefficient_of_variation
    from round2a_cv_of_cv_feasibility import cv_of_cvs
    x = np.array([10.0, 20.0, 15.0, 25.0])
    cv = coefficient_of_variation(x)
    assert cv is not None and cv > 0
    cvs = np.array([0.3, 0.4, 0.5, 0.6])
    assert abs(cv_of_cvs(cvs) - (cvs.std(ddof=1) / cvs.mean())) < 1e-12


# --------------------------------------------------------------------------- scale invariance
def test_C_g_unaffected_by_multiplicative_rescaling_of_one_series():
    """Each constituent CV is scale-invariant (docs/METRIC_PROPERTIES.md);
    rescaling one series' raw abundance values should not change C_g."""
    rows = []
    for plot in range(16):
        for y in range(2000, 2010):
            rows.append([1, plot, "Air", y, 10.0 + plot + (y % 4)])
    keys = [(1, p, "Air") for p in range(16)]
    hist_years = list(range(2000, 2010))
    usable = _synthetic_usable(rows)
    constituents = h4.constituent_series_for_window(usable, keys, 1, hist_years)
    cg_base = h4.compute_C_g(usable, constituents, hist_years)

    scaled_rows = [
        [ds, p, s, y, n * 1000.0 if p == 0 else n]
        for ds, p, s, y, n in rows
    ]
    usable_scaled = _synthetic_usable(scaled_rows)
    cg_scaled = h4.compute_C_g(usable_scaled, constituents, hist_years)
    assert abs(cg_base - cg_scaled) < 1e-9


# --------------------------------------------------------------------------- study-window unit construction
def test_build_h4_row_assembles_from_supplied_values_only():
    row = h4.build_h4_row(1, 1.5, {"baseline_mean_log1p": 2.0, "baseline_cv": 0.5,
                                    "baseline_trend": 0.01, "baseline_n": 8, "baseline_span": 9}, -0.02)
    assert row["DataSource_ID"] == 1
    assert row["C_g"] == 1.5
    assert row["outcome"] == -0.02


# --------------------------------------------------------------------------- permutation reproducibility / exchangeability
def test_permute_study_level_mapping_deterministic():
    cg_by_study = {1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0, 5: 5.0}
    ids = np.array(list(cg_by_study.keys()))
    p1 = h4.permute_study_level_mapping(ids, cg_by_study, seed=42)
    p2 = h4.permute_study_level_mapping(ids, cg_by_study, seed=42)
    assert p1 == p2


def test_permute_study_level_mapping_preserves_value_multiset():
    cg_by_study = {1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0}
    ids = np.array(list(cg_by_study.keys()))
    permuted = h4.permute_study_level_mapping(ids, cg_by_study, seed=0)
    assert sorted(permuted.values()) == sorted(cg_by_study.values())


def test_permute_study_level_mapping_different_seeds_can_differ():
    cg_by_study = {i: float(i) for i in range(10)}
    ids = np.array(list(cg_by_study.keys()))
    p1 = h4.permute_study_level_mapping(ids, cg_by_study, seed=1)
    p2 = h4.permute_study_level_mapping(ids, cg_by_study, seed=2)
    assert p1 != p2


# --------------------------------------------------------------------------- LOSO fold construction
def test_loso_folds_one_fold_per_study():
    groups = np.array([1, 1, 2, 2, 3, 3, 4, 4])
    folds = h4.loso_folds(groups)
    assert len(folds) == 4
    test_groups_seen = set()
    for _, test_idx in folds:
        tg = set(groups[test_idx])
        assert len(tg) == 1  # each test fold is exactly one study
        test_groups_seen |= tg
    assert test_groups_seen == {1, 2, 3, 4}


# --------------------------------------------------------------------------- fit/RMSE machinery (synthetic)
def test_fit_and_pool_rmse_recovers_signal_synthetic():
    rng = np.random.default_rng(7)
    n = 100
    X = rng.normal(size=(n, 2))
    y = 2.0 * X[:, 0] + rng.normal(scale=0.05, size=n)
    groups = np.repeat(np.arange(20), 5)
    rmse = h4.fit_and_pool_rmse(X, y, groups)
    assert rmse < 0.5  # strong signal -> low error


def test_permutation_p_value_formula():
    observed = 0.01
    null = np.array([-0.02, -0.01, 0.0, 0.02, 0.03])  # 2 of 5 >= observed
    p = h4.permutation_p_value(observed, null)
    assert abs(p - (1 + 2) / (5 + 1)) < 1e-12


# --------------------------------------------------------------------------- support-rule logic (synthetic only)
def test_h4_verdict_supported():
    assert h4.h4_verdict(20, delta_rmse=0.01, p_value=0.01) == "SUPPORTED"


def test_h4_verdict_not_supported_wrong_direction_significant_p():
    # significant p but delta_rmse negative -> NOT SUPPORTED, not SUPPORTED
    assert h4.h4_verdict(20, delta_rmse=-0.01, p_value=0.01) == "NOT SUPPORTED"


def test_h4_verdict_not_supported_nonsignificant():
    assert h4.h4_verdict(20, delta_rmse=0.01, p_value=0.5) == "NOT SUPPORTED"


def test_h4_verdict_directionally_opposite():
    result = h4.h4_verdict(20, delta_rmse=-0.02, p_value=0.9, p_value_opposite=0.001)
    assert result == "DIRECTIONALLY OPPOSITE"


def test_h4_verdict_blocked_too_few_studies():
    assert h4.h4_verdict(5, delta_rmse=0.05, p_value=0.001) == "UNINTERPRETABLE / BLOCKED"


def test_h4_verdict_blocked_takes_priority_over_everything():
    assert h4.h4_verdict(9, delta_rmse=0.1, p_value=0.0001) == "UNINTERPRETABLE / BLOCKED"
    assert h4.h4_verdict(10, delta_rmse=0.1, p_value=0.0001) == "SUPPORTED"


# --------------------------------------------------------------------------- machine-readable protocol consistency
def test_h4_protocol_json_matches_frozen_module_constants():
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "protocols", "h4_protocol.json")
    with open(path) as f:
        proto = json.load(f)
    assert proto["minimum_constituent_series"] == h4.MIN_CONSTITUENT_SERIES
    assert proto["historical_window_years"] == h4.HISTORICAL_WINDOW_YEARS
    assert proto["permutation_procedure"]["permutation_count"] == h4.PERMUTATION_COUNT
    assert proto["permutation_procedure"]["seed"] == h4.SEED
    assert proto["alpha"] == h4.ALPHA
    assert proto["baseline_model_M0"] == h4.BASELINE_COLS
    assert proto["augmented_model_M1"] == h4.AUGMENTED_COLS
    assert proto["executed"] is False


def test_h4_protocol_json_chronology_and_predictor_fields_present():
    import json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "protocols", "h4_protocol.json")
    with open(path) as f:
        proto = json.load(f)
    assert proto["chronology_design"] == "C"
    assert proto["parent_feasibility_commit"] == "d3246d9"
    assert proto["predicted_direction"]["sign_on_C_g_coefficient"] == "positive"
    assert proto["support_rule"]["SUPPORTED"]


# --------------------------------------------------------------------------- H4 freeze no-peeking guard
def test_h4_no_peeking_guard():
    import h4_no_peeking_guard as guard
    result = guard.run()
    assert result["H4_NO_PEEKING_CONFIRMED"] is True, result["forbidden_pattern_hits"]
