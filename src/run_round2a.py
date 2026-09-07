#!/usr/bin/env python3
"""ROUND 2A orchestration -- runs Tasks 3-11's structural/support audits
and writes every associated result file. No predictor-outcome association
is computed anywhere in this script (see docs/CV_OF_CV_EARLY_WARNING_CONCEPT.md,
results/ROUND2A_NO_PEEKING_AUDIT.md)."""
from __future__ import annotations

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round2a_cv_of_cv_feasibility as f  # noqa: E402


def main():
    usable, eligibility, eligible = f.load_usable_and_eligibility()
    tables = f.load_tables()

    # ---- Task 3 ----
    study_support = f.study_multiseries_support(usable, eligibility)
    thresholds = f.support_thresholds(study_support)
    study_support.to_json("results/cv_of_cv_study_support_table.json", orient="records", indent=2)
    with open("results/cv_of_cv_study_support.json", "w") as fh:
        json.dump({"threshold_summary": thresholds, "n_studies_with_eligible_series": int((study_support["n_eligible_series"] > 0).sum())}, fh, indent=2)
    write_study_support_md(study_support, thresholds)

    # ---- Task 4 ----
    contemp = f.contemporaneous_counts(usable, eligible)
    contemp_summary = f.contemporaneous_summary(contemp)
    runs = {str(t): f.consecutive_year_runs(contemp, t) for t in [2, 3, 5, 10]}
    with open("results/cv_of_cv_temporal_overlap.json", "w") as fh:
        json.dump({"contemporaneous_summary": contemp_summary, "consecutive_runs_by_threshold": runs}, fh, indent=2)
    write_temporal_overlap_md(contemp_summary, runs)

    # ---- Task 5 ----
    windows = f.window_feasibility(usable, eligible)
    with open("results/cv_of_cv_window_feasibility.json", "w") as fh:
        json.dump(windows, fh, indent=2)
    write_window_feasibility_md(windows)

    # ---- Task 6 ----
    cv_pool = f.historical_cv_pool(usable, eligible)
    stability = f.estimator_stability(cv_pool)
    with open("results/cv_of_cv_estimator_stability.json", "w") as fh:
        json.dump({"pool_size": int(len(cv_pool)), "pool_mean": float(cv_pool.mean()), "pool_sd": float(cv_pool.std(ddof=1)),
                   "bootstrap_resamples": f.BOOTSTRAP_RESAMPLES, "seed": f.BOOTSTRAP_SEED, "by_group_size": stability}, fh, indent=2)
    write_estimator_stability_md(cv_pool, stability)

    # ---- Task 8 ----
    level_change = f.level_vs_change_feasibility(usable, eligible)
    with open("results/cv_of_cv_level_vs_change.json", "w") as fh:
        json.dump(level_change, fh, indent=2)
    write_level_vs_change_md(level_change)

    # ---- Task 10 ----
    chronology = f.chronology_design_feasibility(usable, eligible)
    with open("results/cv_of_cv_chronology_feasibility.json", "w") as fh:
        json.dump(chronology, fh, indent=2)
    write_chronology_md(chronology)

    # ---- Task 11 ----
    heterogeneity = f.context_heterogeneity_audit(tables, study_support, contemp)
    heterogeneity.to_json("results/cv_of_cv_context_audit_table.json", orient="records", indent=2)
    write_context_audit_md(heterogeneity)

    print("Round 2A structural audits complete.")
    print("studies with >=1 eligible series:", int((study_support["n_eligible_series"] > 0).sum()))
    print("studies with >=5 eligible series:", thresholds["5"]["n_studies"])
    print("studies with >=5 contemporaneous eligible series in >=1 year:",
          contemp_summary["studies_ever_achieving_threshold"]["5"])


def write_study_support_md(study_support, thresholds):
    n_with_any = int((study_support["n_eligible_series"] > 0).sum())
    lines = [
        "# CV-of-CVs study-level multi-series support audit (ROUND 2A, Task 3)",
        "",
        f"Studies with >=1 Round-1-eligible abundance series: **{n_with_any}** "
        f"(of {study_support.shape[0]} studies with >=1 candidate abundance series).",
        "",
        "| min eligible series per study | studies meeting | series represented |",
        "|---:|---:|---:|",
    ]
    for k, v in thresholds.items():
        lines.append(f"| {k} | {v['n_studies']} | {v['n_series_represented']} |")
    with open("results/CV_OF_CV_STUDY_SUPPORT.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_temporal_overlap_md(summary, runs):
    lines = ["# CV-of-CVs temporal (contemporaneous) overlap audit (ROUND 2A, Task 4)", "",
              "One row per (study, year); value = number of Round-1-eligible series with "
              "a usable observation that year.", "",
              f"- distribution: min={summary['distribution']['min']}, max={summary['distribution']['max']}, "
              f"mean={summary['distribution']['mean']:.3f}, median={summary['distribution']['median']}",
              "",
              "| threshold | study-years meeting | studies ever achieving | studies sustaining (>=2 yrs) |",
              "|---:|---:|---:|---:|"]
    for t in f.CONTEMPORANEOUS_THRESHOLDS:
        t = str(t)
        lines.append(f"| {t} | {summary['study_year_threshold_counts'][t]} | "
                     f"{summary['studies_ever_achieving_threshold'][t]} | "
                     f"{summary['studies_sustaining_threshold_multiple_years'][t]} |")
    lines += ["", "## Consecutive-year runs meeting each threshold", "",
              "| threshold | studies with run >=3 | >=5 | >=7 | >=10 |", "|---:|---:|---:|---:|---:|"]
    for t, r in runs.items():
        c = r["n_studies_with_run_at_least"]
        lines.append(f"| {t} | {c['3']} | {c['5']} | {c['7']} | {c['10']} |")
    with open("results/CV_OF_CV_TEMPORAL_OVERLAP.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_window_feasibility_md(windows):
    lines = ["# CV-of-CVs historical window feasibility audit (ROUND 2A, Task 5)", ""]
    for W, d in windows.items():
        lines.append(f"## {W}-year windows")
        lines.append(f"- non-overlapping windows total: {d['n_nonoverlapping_windows_total']}, "
                     f"rolling windows total: {d['n_rolling_windows_total']}")
        lines.append("| min series in window | non-overlapping windows meeting | rolling windows meeting |")
        lines.append("|---:|---:|---:|")
        for t in f.WINDOW_SERIES_THRESHOLDS:
            lines.append(f"| {t} | {d['nonoverlapping_meeting_threshold'][str(t)]} | {d['rolling_meeting_threshold'][str(t)]} |")
        lines.append("")
    with open("results/CV_OF_CV_WINDOW_FEASIBILITY.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_estimator_stability_md(cv_pool, stability):
    lines = ["# CV-of-CVs estimator stability audit (ROUND 2A, Task 6)", "",
              f"Historical per-series CV pool: n={len(cv_pool)}, mean={cv_pool.mean():.4f}, "
              f"sd={cv_pool.std(ddof=1):.4f}. Bootstrap: {f.BOOTSTRAP_RESAMPLES} resamples "
              f"per group size, seed={f.BOOTSTRAP_SEED} (frozen before this task ran).",
              "",
              "| n | freq undefined | freq near-zero denom | mean estimate | SD across resamples | 95% CI width | mean single-extreme shift |",
              "|---:|---:|---:|---:|---:|---:|---:|"]
    for n, d in stability.items():
        if "note" in d:
            lines.append(f"| {n} | {d['note']} | | | | | |")
            continue
        lines.append(f"| {n} | {d['frequency_undefined']:.3f} | {d['frequency_near_zero_denominator']:.3f} | "
                     f"{d['mean_estimate']:.4f} | {d['sd_of_estimate_across_resamples']:.4f} | "
                     f"{d['ci_width']:.4f} | {d['mean_single_extreme_sensitivity_shift']:.4f} |")
    with open("results/CV_OF_CV_ESTIMATOR_STABILITY.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_level_vs_change_md(lc):
    lines = ["# CV-of-CVs LEVEL vs CHANGE feasibility (ROUND 2A, Task 8)", "",
              f"Window length used for this feasibility check: {lc['level_window_years']} years; "
              f"minimum series per window: {lc['level_min_series']} (disclosed defaults, not chosen from outcome).",
              "",
              "## LEVEL",
              f"- studies with >=1 adequate historical window: "
              f"{lc['level_feasibility']['n_studies_with_at_least_one_adequate_window']} / "
              f"{lc['level_feasibility']['n_studies_total_with_eligible_series']}",
              "",
              "## CHANGE", "",
              "| min sequential adequate windows | studies meeting |", "|---:|---:|"]
    for m, n in lc["change_feasibility"].items():
        lines.append(f"| {m} | {n} |")
    with open("results/CV_OF_CV_LEVEL_VS_CHANGE.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_chronology_md(chronology):
    lines = ["# CV-of-CVs chronological separation design feasibility (ROUND 2A, Task 10)", "",
              "Structural only -- no outcome value is read. Historical-portion adequacy uses "
              "the same >=5-series / >=2-observations-per-series criteria as Task 8.", ""]
    for name, d in chronology.items():
        lines.append(f"## {name}")
        lines.append(f"- studies retained: {d['n_studies_retained']}")
        lines.append(f"- median future years available: {d['median_future_years_available']}")
        lines.append(f"- leakage risk: {d['leakage_risk']}")
        lines.append("")
    with open("results/CV_OF_CV_CHRONOLOGY_FEASIBILITY.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_context_audit_md(het):
    lines = ["# CV-of-CVs context/heterogeneity audit (ROUND 2A, Task 11)", "",
              "Cross-tabulates whether a study meets the >=5-contemporaneous-eligible-series "
              "threshold (any year, Task 4) against study metadata. Feasibility/confounding "
              "audit only -- no outcome value is referenced.", ""]
    for col in ["Realm", "AbundanceOrBiomass"]:
        lines.append(f"## by `{col}`")
        tab = het.groupby(col)["meets_contemporaneous_5_threshold_any_year"].agg(["sum", "count"])
        lines.append("| value | meets threshold | total studies |")
        lines.append("|---|---:|---:|")
        for idx, row in tab.iterrows():
            lines.append(f"| {idx} | {int(row['sum'])} | {int(row['count'])} |")
        lines.append("")
    lines.append("## duration_years, n_plots_in_source, n_distinct_sampling_methods by threshold status")
    g = het.groupby("meets_contemporaneous_5_threshold_any_year")[["duration_years", "n_plots_in_source", "n_distinct_sampling_methods"]].median()
    lines.append(g.to_markdown() if hasattr(g, "to_markdown") else str(g))
    with open("results/CV_OF_CV_CONTEXT_AUDIT.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
