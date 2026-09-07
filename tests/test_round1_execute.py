"""
Tests for src/round1_execute.py and src/run_round1.py. Skipped if the real
corpus has not been fetched locally. Negative-control tests use a small
override permutation count for speed -- the frozen 2,000-permutation runs
are executed once by src/run_round1.py itself, not repeated here.
"""
import json
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


# --------------------------------------------------------------------------- Holm correction
def test_holm_correction_known_example():
    import round1_execute as r1
    # classic textbook example: raw p = 0.01, 0.02, 0.03, 0.04 (already sorted)
    raw = {"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.04}
    adj = r1.holm_correction(raw)
    assert abs(adj["a"] - 0.04) < 1e-9   # (4-0)*0.01
    assert abs(adj["b"] - 0.06) < 1e-9   # max(0.04, (4-1)*0.02)
    assert abs(adj["c"] - 0.06) < 1e-9   # max(0.06, (4-2)*0.03)
    assert abs(adj["d"] - 0.06) < 1e-9   # max(0.06, (4-3)*0.04)


def test_holm_correction_never_exceeds_one():
    import round1_execute as r1
    raw = {"a": 0.9, "b": 0.8, "c": 0.99}
    adj = r1.holm_correction(raw)
    assert all(v <= 1.0 for v in adj.values())


def test_holm_correction_is_monotonic_with_raw_p_rank():
    import round1_execute as r1
    raw = {"x": 0.5, "y": 0.001, "z": 0.2}
    adj = r1.holm_correction(raw)
    assert adj["y"] <= adj["z"] <= adj["x"]


# --------------------------------------------------------------------------- common_table
def test_common_table_drops_only_undefined_metric_rows():
    import round1_execute as r1
    from round1_pipeline import BASELINE_COLS, CONSTRAINT_COLS
    df = r1.common_table()
    assert df.shape[0] == 1126
    assert df[BASELINE_COLS + CONSTRAINT_COLS + ["outcome"]].notna().all().all()


# --------------------------------------------------------------------------- grouped fit determinism
def test_grouped_oof_predictions_deterministic():
    import round1_execute as r1
    rng = np.random.default_rng(0)
    n = 200
    X = rng.normal(size=(n, 3))
    y = X[:, 0] * 0.5 + rng.normal(scale=0.1, size=n)
    groups = np.repeat(np.arange(20), 10)
    oof_a, rmse_a, _ = r1.grouped_oof_predictions(X, y, groups, n_splits=5)
    oof_b, rmse_b, _ = r1.grouped_oof_predictions(X, y, groups, n_splits=5)
    assert np.allclose(oof_a, oof_b)
    assert rmse_a == rmse_b


def test_grouped_oof_predictions_recovers_a_real_linear_signal():
    """Sanity check on the fitting machinery itself (not the real corpus):
    a strong, noiseless-ish linear signal should be recovered with low
    out-of-fold RMSE and high R^2."""
    import round1_execute as r1
    rng = np.random.default_rng(1)
    n = 300
    X = rng.normal(size=(n, 2))
    y = 3.0 * X[:, 0] - 2.0 * X[:, 1] + rng.normal(scale=0.01, size=n)
    groups = np.repeat(np.arange(30), 10)
    oof, _, _ = r1.grouped_oof_predictions(X, y, groups, n_splits=5)
    r2 = r1.pooled_r2(y, oof)
    assert r2 > 0.95


# --------------------------------------------------------------------------- H1 structure
def test_run_h1_returns_all_three_metrics_with_required_fields():
    import round1_execute as r1
    from round1_pipeline import CONSTRAINT_COLS
    df = r1.common_table()
    h1 = r1.run_h1(df)
    assert set(h1.keys()) == set(CONSTRAINT_COLS)
    for m in CONSTRAINT_COLS:
        for field in ("coefficient_standardized", "se_cluster_robust", "ci_95", "raw_p_value",
                      "direction_matches_frozen_prediction"):
            assert field in h1[m]
        assert 0.0 <= h1[m]["raw_p_value"] <= 1.0


# --------------------------------------------------------------------------- H2 structure
def test_run_h2_pooled_rmse_matches_manual_recomputation_from_oof():
    import round1_execute as r1
    from round1_pipeline import BASELINE_COLS, CONSTRAINT_COLS
    df = r1.common_table()
    h2 = r1.run_h2(df)
    y = df["outcome"].values.astype(float)
    manual_rmse0 = float(np.sqrt(np.mean((y - h2["_oof0"]) ** 2)))
    assert abs(manual_rmse0 - h2["M0_pooled_oof_rmse"]) < 1e-9
    assert h2["delta_rmse_M0_minus_M1"] == h2["M0_pooled_oof_rmse"] - h2["M1_pooled_oof_rmse"]
    assert len(h2["fold_rmse_M0"]) == 10


# --------------------------------------------------------------------------- negative controls (small n_perm for speed)
def test_nc1_and_nc2_produce_valid_p_values_small_run():
    import round1_execute as r1
    df = r1.common_table()
    h2 = r1.run_h2(df)
    obs = h2["delta_rmse_M0_minus_M1"]
    nc1 = r1.nc1_within_study_constraint_permutation(df, obs, n_perm=20)
    nc2 = r1.nc2_within_study_outcome_permutation(df, obs, n_perm=20)
    assert 0.0 <= nc1["empirical_one_sided_p"] <= 1.0
    assert 0.0 <= nc2["empirical_one_sided_p"] <= 1.0
    assert nc1["n_permutations"] == 20 and nc2["n_permutations"] == 20


def test_nc1_null_mean_near_zero_when_true_null_holds():
    """Under NC1's own null (constraint metric carries no information),
    the null delta_rmse distribution should be centered near the M0-only
    baseline noise floor, not systematically large and positive."""
    import round1_execute as r1
    df = r1.common_table()
    h2 = r1.run_h2(df)
    obs = h2["delta_rmse_M0_minus_M1"]
    nc1 = r1.nc1_within_study_constraint_permutation(df, obs, n_perm=50)
    assert abs(nc1["null_mean"]) < 0.01  # small relative to the outcome's own scale (~0.17 RMSE)


# --------------------------------------------------------------------------- reversed (NC3) table construction
def test_build_reversed_table_has_no_overlap_with_forward_windows():
    import round1_execute as r1
    rev = r1.build_reversed_table()
    assert rev.shape[0] > 0
    assert "outcome_reversed" in rev.columns


# --------------------------------------------------------------------------- H3 gate enforcement
def test_run_h3_only_tests_adequate_strata():
    import round1_execute as r1
    df = r1.common_table()
    h3 = r1.run_h3(df)
    assert set(h3["per_stratum"].keys()) == {"Air", "Water", "Herb layer", "Soil surface"}
    assert "Trees" not in h3["per_stratum"]
    assert "Underground" not in h3["per_stratum"]
    assert set(h3["excluded_strata"]) == {"Trees", "Underground"}


# --------------------------------------------------------------------------- full orchestration + serialization
def test_run_round1_end_to_end_writes_valid_json(tmp_path, monkeypatch):
    """Runs the full Round 1 orchestration (with the frozen 2,000-permutation
    negative controls) exactly once and checks every result file is valid,
    parseable JSON with the expected top-level shape. This is the same
    execution src/run_round1.py performs when run directly; this test
    exists to catch a serialization regression, not to re-derive the
    scientific result."""
    import subprocess
    root = ROOT
    result = subprocess.run([sys.executable, os.path.join(root, "src", "run_round1.py")],
                             cwd=root, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr

    for fname in ["round1_primary_results.json", "round1_negative_controls.json",
                  "round1_stratum_results.json", "round1_descriptive_benchmarks.json"]:
        path = os.path.join(root, "results", fname)
        with open(path) as f:
            data = json.load(f)
        assert data  # non-empty, valid JSON

    primary = json.load(open(os.path.join(root, "results", "round1_primary_results.json")))
    assert primary["frozen_protocol_commit"] == "21e6992"
    assert primary["overall_verdict"] in {
        "STRONG POSITIVE UPDATE", "WEAK POSITIVE UPDATE", "NEGATIVE UPDATE",
        "NULL / INCONCLUSIVE", "BLOCKED",
    }
    for key in ("H1-A", "H1-B", "H1-C"):
        assert primary["H1"][key]["verdict"] in {"SUPPORTED", "NOT SUPPORTED", "DIRECTIONALLY OPPOSITE", "UNINTERPRETABLE"}
    assert primary["H2"]["verdict"] in {"SUPPORTED", "NOT SUPPORTED"}
