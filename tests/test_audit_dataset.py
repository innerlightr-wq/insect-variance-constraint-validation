"""
Tests for src/audit_dataset.py. Skipped if the real corpus has not been
fetched locally (see tests/test_data_integration.py for the same skip
condition and rationale).
"""
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
DATA_DIR = os.path.join(ROOT, "data", "raw", "insect_knb")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv")),
    reason="data/raw/insect_knb/ not present locally -- see data/README.md to fetch it",
)


def test_schema_audit_matches_frozen_provenance_numbers():
    import audit_dataset as ad
    tables = ad.load_raw(DATA_DIR)
    audit = ad.schema_audit(tables)
    assert audit["unique_studies_DataSource_ID"] == 166
    assert audit["unique_plots_Plot_ID"] == 1676
    assert audit["year_coverage"] == {"min": 1925, "max": 2018}
    assert audit["metric_field"]["abundance_rows"] == 64152
    assert audit["metric_field"]["biomass_rows"] == 6803
    ri = audit["referential_integrity"]
    assert ri["plot_datasource_id_mismatches_between_tables"] == 0
    assert ri["duplicate_plot_id_rows_in_plotdata"] == 0
    assert ri["duplicate_datasource_id_rows_in_datasources"] == 0


def test_schema_audit_reports_no_negative_abundance_values():
    import audit_dataset as ad
    tables = ad.load_raw(DATA_DIR)
    audit = ad.schema_audit(tables)
    assert audit["abundance_value_field_Number"]["n_negative"] == 0
