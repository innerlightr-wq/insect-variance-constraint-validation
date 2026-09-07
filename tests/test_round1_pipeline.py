"""
Tests for src/round1_pipeline.py. Skipped if the real corpus has not been
fetched locally.
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
DATA_DIR = os.path.join(ROOT, "data", "raw", "insect_knb")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv")),
    reason="data/raw/insect_knb/ not present locally -- see data/README.md to fetch it",
)


def test_build_modeling_table_matches_frozen_eligible_count():
    import round1_pipeline as rp
    tbl = rp.build_modeling_table()
    assert tbl.shape[0] == 1129


def test_leakage_check_passes_on_real_table():
    import round1_pipeline as rp
    tbl = rp.build_modeling_table()
    checks = rp.leakage_check(tbl)
    assert all(checks.values())


def test_early_window_never_overlaps_late_window():
    import round1_pipeline as rp
    tbl = rp.build_modeling_table()
    assert (tbl["early_year_max"] < tbl["late_year_min"]).all()


def test_series_row_uses_only_early_window_for_predictors_synthetic():
    """Construct a synthetic series where the early and late windows have
    deliberately different distributions; verify the returned predictors
    match a manual computation from the early window ONLY."""
    import pandas as pd
    from round1_pipeline import series_row
    from insect_variance_protocol import coefficient_of_variation

    years = list(range(2000, 2010))  # 10 years -> early = first 5, late = last 5
    early_vals = [10.0, 12.0, 11.0, 9.0, 10.0]
    late_vals = [1000.0, 1000.0, 1000.0, 1000.0, 1000.0]  # wildly different scale
    sub = pd.DataFrame({"Year": years, "Number": early_vals + late_vals})
    row = series_row((1, 1, "Air"), sub)

    expected_mean_log1p = float(np.mean(np.log1p(early_vals)))
    assert abs(row["baseline_mean_log1p"] - expected_mean_log1p) < 1e-9
    expected_cv = coefficient_of_variation(np.array(early_vals))
    assert abs(row["baseline_cv"] - expected_cv) < 1e-9
    # if late-window values leaked in, mean_log1p would be enormous (log1p(1000)~6.9)
    assert row["baseline_mean_log1p"] < 4.0
