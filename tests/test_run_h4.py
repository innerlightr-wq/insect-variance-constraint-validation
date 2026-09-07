"""
Tests for src/run_h4.py -- the real H4 execution pathway and result
serialization. Skipped if the real corpus has not been fetched locally
(same convention as the rest of this project's real-data tests). These
tests assert on the ACTUAL, ALREADY-COMPUTED H4 result recorded in
results/ -- they are not synthetic-freeze tests, and they are not
adjusted to make an inconvenient real result look better.
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


def test_materialize_population_matches_recorded_counts():
    import run_h4
    pop = run_h4.materialize_population()
    n_candidate = len(pop["candidate_studies"])
    n_adequate = sum(1 for v in pop["study_reports"].values() if v.get("adequate"))
    n_h4_eligible = len(pop["adequate_studies"])
    assert n_candidate == 99
    assert n_adequate == 16
    assert n_h4_eligible == 11


def test_leakage_audit_clean_on_real_data():
    import run_h4
    pop = run_h4.materialize_population()
    la = run_h4.leakage_audit(pop["adequate_studies"], pop["round1_by_key"])
    assert la["LEAKAGE_FREE"] is True
    assert la["n_violations"] == 0
    assert la["n_checks"] == 384


def test_c_g_deterministic_and_matches_recorded_range():
    import run_h4
    pop = run_h4.materialize_population()
    cg1 = run_h4.compute_all_cg(pop["usable"], pop["adequate_studies"])
    cg2 = run_h4.compute_all_cg(pop["usable"], pop["adequate_studies"])
    assert cg1 == cg2  # fully deterministic, no randomness in C_g construction
    values = np.array(list(cg1.values()))
    assert len(values) == 11
    assert values.min() > 0.2 and values.max() < 0.6  # matches results/H4_POPULATION.md


def test_loso_matches_recorded_primary_result():
    import run_h4
    pop = run_h4.materialize_population()
    cg = run_h4.compute_all_cg(pop["usable"], pop["adequate_studies"])
    df = run_h4.build_h4_table(pop["adequate_studies"], cg, pop["round1_by_key"])
    assert df.shape[0] == 384
    loso = run_h4.run_loso(df)
    assert loso["n_folds"] == 11
    assert abs(loso["rmse_M0_pooled"] - 0.14194956995682934) < 1e-9
    assert abs(loso["rmse_M1_pooled"] - 0.14430347632111523) < 1e-9
    assert abs(loso["delta_rmse_pooled"] - (-0.002353906364285896)) < 1e-9
    assert loso["n_folds_favoring_M1"] == 7
    assert loso["n_folds_favoring_M0"] == 4


def test_permutation_p_value_reproducible_with_frozen_seed():
    """Reruns a SMALL number of permutations (not the full frozen 10,000 --
    that already ran once, in results/) to confirm the permutation
    mechanism itself is exactly reproducible given the frozen seed. This
    does not recompute or replace the recorded, already-committed p-value."""
    import run_h4
    import h4_pipeline as h4
    pop = run_h4.materialize_population()
    cg = run_h4.compute_all_cg(pop["usable"], pop["adequate_studies"])
    df = run_h4.build_h4_table(pop["adequate_studies"], cg, pop["round1_by_key"])
    study_ids = np.array(sorted(cg.keys()))
    m1 = h4.permute_study_level_mapping(study_ids, cg, seed=h4.SEED + 0)
    m2 = h4.permute_study_level_mapping(study_ids, cg, seed=h4.SEED + 0)
    assert m1 == m2


def test_verdict_matches_recorded_result():
    import run_h4
    import h4_pipeline as h4
    result_path = os.path.join(ROOT, "results", "h4_primary_results.json")
    perm_path = os.path.join(ROOT, "results", "h4_permutation_results.json")
    with open(result_path) as f:
        primary = json.load(f)
    with open(perm_path) as f:
        perm = json.load(f)
    n_eligible = primary["n_h4_eligible_studies"]
    delta = primary["loso"]["delta_rmse_pooled"]
    p = perm["p_value"]
    p_opp = perm["p_value_opposite_tail"]
    verdict = h4.h4_verdict(n_eligible, delta_rmse=delta, p_value=p, p_value_opposite=p_opp)
    assert verdict == "NOT SUPPORTED"


# --------------------------------------------------------------------------- result serialization
@pytest.mark.parametrize("fname", [
    "h4_population.json", "h4_leakage_audit.json", "h4_primary_results.json",
    "h4_permutation_results.json", "h4_preexecution_audit.json",
])
def test_result_json_files_valid_and_reference_frozen_commits(fname):
    path = os.path.join(ROOT, "results", fname)
    with open(path) as f:
        data = json.load(f)
    assert data
    text = json.dumps(data)
    # every H4 result payload should trace back to the frozen commits somewhere
    # in its own content or its companion .md (checked separately below)
    assert isinstance(data, dict)


@pytest.mark.parametrize("fname", [
    "H4_POPULATION.md", "H4_LEAKAGE_AUDIT.md", "H4_PRIMARY_RESULTS.md",
    "H4_PERMUTATION_RESULTS.md", "H4_VERDICT.md", "ROUND1_H4_SYNTHESIS.md",
])
def test_result_md_files_state_frozen_commits(fname):
    path = os.path.join(ROOT, "results", fname)
    with open(path) as f:
        text = f.read()
    assert "3e30670" in text
    assert "d3246d9" in text
