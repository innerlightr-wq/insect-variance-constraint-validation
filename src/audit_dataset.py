#!/usr/bin/env python3
"""
Schema / data-adequacy audit (Task 3). Inspects the real, checksum-verified
raw corpus. Computes ONLY structural/descriptive facts about the data --
row/column counts, missingness, zeros, duplicates, referential integrity,
sampling irregularity, within-year multiplicity, and abundance/biomass
commensurability. Does NOT compute, inspect, or report any relationship
between a candidate constraint metric and the future outcome, and does not
touch the outcome variable's association with any predictor at all (no
peeking).

Usage:
    python3 src/audit_dataset.py --data-dir data/raw/insect_knb \
        --out-md results/DATA_ADEQUACY_AUDIT.md \
        --out-json results/data_adequacy_audit.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from insect_variance_protocol import build_yearly_abundance_table, SERIES_KEY  # noqa: E402

ENCODING = "latin-1"  # confirmed necessary: InsectAbundanceBiomassData.csv is not valid UTF-8


def load_raw(data_dir: str) -> dict:
    return {
        "DataSources": pd.read_csv(os.path.join(data_dir, "DataSources.csv"), encoding=ENCODING),
        "PlotData": pd.read_csv(os.path.join(data_dir, "PlotData.csv"), encoding=ENCODING),
        "SampleData": pd.read_csv(os.path.join(data_dir, "SampleData.csv"), encoding=ENCODING),
        "InsectAbundanceBiomassData": pd.read_csv(
            os.path.join(data_dir, "InsectAbundanceBiomassData.csv"), encoding=ENCODING
        ),
    }


def referential_integrity(tables: dict) -> dict:
    ab, plot, ds = tables["InsectAbundanceBiomassData"], tables["PlotData"], tables["DataSources"]
    plot_ids_in_ab_missing_from_plotdata = sorted(set(ab["Plot_ID"].unique()) - set(plot["Plot_ID"].unique()))
    ds_ids_in_plot_missing_from_datasources = sorted(set(plot["DataSource_ID"].unique()) - set(ds["DataSource_ID"].unique()))
    merged = ab[["DataSource_ID", "Plot_ID"]].drop_duplicates().merge(
        plot[["Plot_ID", "DataSource_ID"]], on="Plot_ID", suffixes=("_ab", "_plot")
    )
    ds_mismatches = int((merged["DataSource_ID_ab"] != merged["DataSource_ID_plot"]).sum())
    return {
        "plot_ids_in_abundance_missing_from_plotdata": len(plot_ids_in_ab_missing_from_plotdata),
        "datasource_ids_in_plotdata_missing_from_datasources": len(ds_ids_in_plot_missing_from_datasources),
        "plot_datasource_id_mismatches_between_tables": ds_mismatches,
        "duplicate_plot_id_rows_in_plotdata": int(plot["Plot_ID"].duplicated().sum()),
        "duplicate_datasource_id_rows_in_datasources": int(ds["DataSource_ID"].duplicated().sum()),
    }


def schema_audit(tables: dict) -> dict:
    ab = tables["InsectAbundanceBiomassData"]
    plot = tables["PlotData"]
    ds = tables["DataSources"]
    samp = tables["SampleData"]

    abundance_rows = ab[ab["MetricAB"] == "abundance"]
    biomass_rows = ab[ab["MetricAB"] == "biomass"]

    # within-year multiplicity (raw, before aggregation)
    per_key_year = ab.groupby(SERIES_KEY + ["Year"]).size()
    multi_period_year_rate = float((per_key_year > 1).mean())

    # commensurability check: does any (DataSource_ID,Plot_ID,Stratum) series
    # mix abundance AND biomass rows?
    combo_counts = ab.groupby(SERIES_KEY)["MetricAB"].nunique()
    n_series_mixing_metric = int((combo_counts > 1).sum())

    # does a plot change SamplingMethod over time? SampleData.csv keys on
    # DataSource_ID only (not Plot_ID), so this is auditable at the
    # study level, not the individual-plot level, in this source -- a
    # disclosed limitation, not silently assumed away.
    sampling_methods_per_study = samp.groupby("DataSource_ID")["SamplingMethod"].nunique()
    n_studies_with_gt1_sampling_method_recorded = int((sampling_methods_per_study > 1).sum())

    return {
        "files": {
            name: {"rows": int(df.shape[0]), "columns": int(df.shape[1])}
            for name, df in tables.items()
        },
        "unique_studies_DataSource_ID": int(ds["DataSource_ID"].nunique()),
        "unique_plots_Plot_ID": int(plot["Plot_ID"].nunique()),
        "year_coverage": {"min": int(ab["Year"].min()), "max": int(ab["Year"].max())},
        "stratum_field": {
            "column": "Stratum",
            "values": ab["Stratum"].value_counts(dropna=False).to_dict(),
        },
        "metric_field": {
            "column": "MetricAB",
            "values": ab["MetricAB"].value_counts(dropna=False).to_dict(),
            "abundance_rows": int(abundance_rows.shape[0]),
            "biomass_rows": int(biomass_rows.shape[0]),
        },
        "abundance_value_field_Number": {
            "n_total_abundance_rows": int(abundance_rows.shape[0]),
            "n_missing": int(abundance_rows["Number"].isna().sum()),
            "missing_rate": float(abundance_rows["Number"].isna().mean()),
            "n_zero": int((abundance_rows["Number"] == 0).sum()),
            "zero_rate_of_non_missing": float(
                (abundance_rows["Number"] == 0).sum() / abundance_rows["Number"].notna().sum()
            ),
            "n_negative": int((abundance_rows["Number"] < 0).sum()),
            "min": float(abundance_rows["Number"].min(skipna=True)),
            "max": float(abundance_rows["Number"].max(skipna=True)),
            "median": float(abundance_rows["Number"].median(skipna=True)),
        },
        "sampling_period_field": {
            "column": "Period",
            "n_unique_values": int(ab["Period"].nunique()),
            "rows_sharing_key_and_year_with_gt1_row_rate": multi_period_year_rate,
            "note": "Period values observed are consistent with sub-annual "
                    "(e.g. monthly) sampling occasions within a calendar "
                    "year, not a validated calendar-month field per se -- "
                    "see docs/DATA_PROVENANCE.md for the exact source "
                    "documentation consulted.",
        },
        "duplicate_records": {
            "exact_duplicate_rows_in_abundance_biomass_table": int(ab.duplicated().sum()),
        },
        "series_mixing_abundance_and_biomass_at_same_key": n_series_mixing_metric,
        "abundance_biomass_commensurability": {
            "pooled_directly": False,
            "reason": "abundance (counts) and biomass (mass) are different "
                      "physical quantities on different scales across "
                      "different original studies -- never pooled into one "
                      "series or one model; abundance is the frozen primary "
                      "analysis (Task 5), biomass is reserved for a "
                      "separately-run sensitivity analysis only.",
        },
        "sampling_method_stability": {
            "granularity_available_in_source": "DataSource_ID (study-level), "
                                                "not Plot_ID (plot-level) -- "
                                                "SampleData.csv has no "
                                                "Plot_ID column",
            "n_studies_with_more_than_one_recorded_sampling_method": n_studies_with_gt1_sampling_method_recorded,
            "n_studies_total_in_sampledata": int(samp["DataSource_ID"].nunique()),
        },
        "referential_integrity": referential_integrity(tables),
        "geographic_fields_present": [c for c in ["Latitude", "Longitude", "Elevation"] if c in plot.columns],
        "taxonomic_field_present": "InvertebrateGroup" in ds.columns,
        "treatment_control_field_present": "ExperimentalTreatment" in plot.columns,
    }


def write_report(audit: dict, out_md: str, out_json: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)

    f_ = audit["files"]
    lines = [
        "# Data adequacy audit — van Klink et al. (2020) insect assemblage database",
        "",
        "**Schema/structure audit only. No association between any candidate "
        "constraint metric and the future outcome is computed or inspected "
        "here (no peeking).** Source: `docs/DATA_PROVENANCE.md`. Generated "
        "by `src/audit_dataset.py` from the checksum-verified raw files in "
        "`data/raw/insect_knb/`.",
        "",
        "## File / row / column counts",
        "",
        "| file | rows | columns |",
        "|---|---:|---:|",
    ]
    for name, info in f_.items():
        lines.append(f"| {name}.csv | {info['rows']} | {info['columns']} |")
    lines += [
        "",
        f"- Unique studies (`DataSource_ID`): **{audit['unique_studies_DataSource_ID']}**",
        f"- Unique plots (`Plot_ID`): **{audit['unique_plots_Plot_ID']}**",
        f"- Year coverage: **{audit['year_coverage']['min']}–{audit['year_coverage']['max']}**",
        "",
        "## Ecological stratum field (`Stratum`)",
        "",
        "| stratum | rows |",
        "|---|---:|",
    ]
    for k, v in audit["stratum_field"]["values"].items():
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "## Abundance vs. biomass (`MetricAB`)",
        "",
        f"- abundance rows: **{audit['metric_field']['abundance_rows']}**",
        f"- biomass rows: **{audit['metric_field']['biomass_rows']}**",
        f"- series mixing both metrics at the same (study, plot, stratum) key: "
        f"**{audit['series_mixing_abundance_and_biomass_at_same_key']}**",
        "- **Not pooled**: " + audit["abundance_biomass_commensurability"]["reason"],
        "",
        "## Abundance value field (`Number`), abundance rows only",
        "",
    ]
    nv = audit["abundance_value_field_Number"]
    lines += [
        f"- missing: {nv['n_missing']} / {nv['n_total_abundance_rows']} ({nv['missing_rate']:.1%})",
        f"- exact zero (of non-missing): {nv['n_zero']} ({nv['zero_rate_of_non_missing']:.1%})",
        f"- negative values: {nv['n_negative']}",
        f"- range: [{nv['min']}, {nv['max']}], median {nv['median']}",
        "",
        "## Sampling irregularity",
        "",
        f"- distinct `Period` values observed: {audit['sampling_period_field']['n_unique_values']}",
        f"- (study, plot, stratum, year) combinations with more than one raw "
        f"row (multiple within-year sampling periods): "
        f"{audit['sampling_period_field']['rows_sharing_key_and_year_with_gt1_row_rate']:.1%}",
        "- Frozen handling rule: `insect_variance_protocol.aggregate_within_year` "
        "sums `Number` across periods within a (study, plot, stratum, year) "
        "cell; a cell with all-null periods is left null, never coerced to "
        "zero. See `docs/HYPOTHESIS_PROTOCOL.md`.",
        "",
        "## Referential integrity",
        "",
    ]
    ri = audit["referential_integrity"]
    for k, v in ri.items():
        lines.append(f"- {k}: {v}")
    lines += [
        "",
        "## Duplicates",
        "",
        f"- exact duplicate rows in `InsectAbundanceBiomassData.csv`: "
        f"{audit['duplicate_records']['exact_duplicate_rows_in_abundance_biomass_table']}",
        "",
        "## Sampling-method stability",
        "",
        f"- granularity available in source: "
        f"{audit['sampling_method_stability']['granularity_available_in_source']}",
        f"- studies with more than one recorded sampling method: "
        f"{audit['sampling_method_stability']['n_studies_with_more_than_one_recorded_sampling_method']} "
        f"/ {audit['sampling_method_stability']['n_studies_total_in_sampledata']}",
        "- **Disclosed limitation**: this source cannot audit whether a single "
        "*plot's* sampling method changed over time — only whether a *study* "
        "recorded more than one method overall. A plot-level check is not "
        "available without external data.",
        "",
        "## Other fields present",
        "",
        f"- geographic fields in PlotData.csv: {audit['geographic_fields_present']}",
        f"- taxonomic field in DataSources.csv (`InvertebrateGroup`): "
        f"{audit['taxonomic_field_present']}",
        f"- treatment/control field in PlotData.csv (`ExperimentalTreatment`): "
        f"{audit['treatment_control_field_present']}",
    ]
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/raw/insect_knb")
    ap.add_argument("--out-md", default="results/DATA_ADEQUACY_AUDIT.md")
    ap.add_argument("--out-json", default="results/data_adequacy_audit.json")
    args = ap.parse_args()

    tables = load_raw(args.data_dir)
    audit = schema_audit(tables)
    write_report(audit, args.out_md, args.out_json)
    print(f"wrote {args.out_md} and {args.out_json}")


if __name__ == "__main__":
    main()
