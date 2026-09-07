"""
Integration tests against the real, downloaded corpus. Skipped entirely if
`data/raw/insect_knb/` has not been fetched locally (it is gitignored, per
`data/README.md`) -- these tests never fabricate or substitute data. They
verify provenance/checksum integrity and that the schema/power-adequacy
audits run and report the exact frozen numbers this round's protocol
documents cite. They do NOT test any predictor-outcome association.
"""
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
DATA_DIR = os.path.join(ROOT, "data", "raw", "insect_knb")

pytestmark = pytest.mark.skipif(
    not os.path.isdir(DATA_DIR) or not os.path.exists(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv")),
    reason="data/raw/insect_knb/ not present locally -- see data/README.md to fetch it",
)


def _provenance():
    with open(os.path.join(ROOT, "data", "provenance.json")) as f:
        return json.load(f)


def test_all_downloaded_files_match_declared_md5():
    import insect_variance_protocol as ivp
    prov = _provenance()
    for entry in prov["files"]:
        if "md5_reported_by_dataone" not in entry:
            continue
        path = os.path.join(DATA_DIR, entry["entity_name"])
        assert ivp.verify_checksum(path, entry["md5_reported_by_dataone"]), entry["entity_name"]


def test_all_downloaded_files_match_declared_sha256():
    import insect_variance_protocol as ivp
    prov = _provenance()
    for entry in prov["files"]:
        path = os.path.join(DATA_DIR, entry["entity_name"])
        assert ivp.sha256_of_file(path) == entry["sha256_computed_locally"], entry["entity_name"]


def test_manuscript_scale_claims_hold_against_real_files():
    import pandas as pd
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding="latin-1")
    prov = _provenance()
    claims = prov["manuscript_scale_claims_independent_verification"]
    assert ab.shape[0] == claims["verified_observations_InsectAbundanceBiomassData_rows"]
    assert ab["Plot_ID"].nunique() == claims["verified_unique_Plot_ID_in_abundance_biomass_table"]


def test_power_adequacy_audit_runs_and_matches_frozen_protocol_numbers():
    import power_adequacy_audit as paa
    result = paa.run()
    assert result["eligibility"]["n_eligible"] == 1129
    assert result["studies"]["n_eligible_studies"] == 99
    assert result["gate"]["verdict"] == "READY"
    assert result["grouped_fold_report"]["n_splits_used"] == 10
    assert result["grouped_fold_report"]["fallback_triggered"] is False


def test_stratum_adequacy_gate_matches_frozen_protocol_table():
    import power_adequacy_audit as paa
    result = paa.run()
    rows = {r["Stratum"]: r for r in result["stratum_adequacy_gate"]}
    assert rows["Air"]["n_series"] == 406 and rows["Air"]["adequate_for_H3"] is True
    assert rows["Water"]["n_series"] == 328 and rows["Water"]["adequate_for_H3"] is True
    assert rows["Trees"]["adequate_for_H3"] is False
    assert rows["Underground"]["adequate_for_H3"] is False


def test_no_predictor_outcome_association_computed_in_power_audit_source():
    """Structural guard: the power-adequacy audit script must never import
    or reference the frozen constraint-metric functions (power_mean_ratio,
    quantile_ratio) -- it is a strict no-peeking, outcome-only-marginal
    audit by design (Task 18)."""
    with open(os.path.join(ROOT, "src", "power_adequacy_audit.py")) as f:
        src = f.read()
    assert "power_mean_ratio" not in src
    assert "quantile_ratio" not in src
