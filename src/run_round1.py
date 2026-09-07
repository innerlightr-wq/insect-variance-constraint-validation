#!/usr/bin/env python3
"""
ROUND 1 orchestration. Runs H1, H2, negative controls, Holm correction,
the primary verdict, H3, and descriptive benchmarks, in that order, and
writes every Task 11 result file. The verdict rule (`determine_verdict`)
is written and fixed BEFORE this script is ever executed against the real
data -- see the function body for the frozen decision rule and its
rationale, disclosed in-line, not adjusted after seeing results.
"""
from __future__ import annotations

import json
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round1_execute as r1  # noqa: E402
from round1_pipeline import BASELINE_COLS, CONSTRAINT_COLS  # noqa: E402

FROZEN_COMMIT = "21e6992"


def determine_verdict(h1_verdicts: dict, h2_verdict: str, h2_delta_rmse: float) -> str:
    """Frozen decision rule (fixed before this script was run against real
    data):
      - H2 gates whether the overall verdict can be POSITIVE at all, per
        Task 8's explicit instruction that incremental out-of-sample value
        is required and a significant individual H1 coefficient alone is
        insufficient.
      - If H2 SUPPORTED: STRONG POSITIVE UPDATE if >=2 of the 3 H1 metrics
        are individually SUPPORTED too; otherwise WEAK POSITIVE UPDATE.
      - If H2 NOT SUPPORTED: NEGATIVE UPDATE if M1 did not even
        descriptively beat M0 (delta_rmse <= 0) OR at least one H1 metric
        is DIRECTIONALLY OPPOSITE and significant; otherwise NULL /
        INCONCLUSIVE (the clean negative-result condition this protocol
        was designed to be capable of returning).
    """
    h1_supported = sum(1 for v in h1_verdicts.values() if v == "SUPPORTED")
    h1_opposite = sum(1 for v in h1_verdicts.values() if v == "DIRECTIONALLY OPPOSITE")

    if h2_verdict == "SUPPORTED":
        return "STRONG POSITIVE UPDATE" if h1_supported >= 2 else "WEAK POSITIVE UPDATE"
    else:
        if h2_delta_rmse <= 0 or h1_opposite >= 1:
            return "NEGATIVE UPDATE"
        return "NULL / INCONCLUSIVE"


def main():
    df = r1.common_table()
    n = df.shape[0]
    n_studies = df["DataSource_ID"].nunique()

    # ---- H1 ----
    h1 = r1.run_h1(df)
    raw_p = {f"H1-{'ABC'[i]}": h1[m]["raw_p_value"] for i, m in enumerate(CONSTRAINT_COLS)}

    # ---- H2 ----
    h2 = r1.run_h2(df)
    h2_delta_rmse = h2["delta_rmse_M0_minus_M1"]
    oof0, oof1 = h2.pop("_oof0"), h2.pop("_oof1")

    # ---- negative controls (target H2) ----
    nc1 = r1.nc1_within_study_constraint_permutation(df, h2_delta_rmse)
    nc2 = r1.nc2_within_study_outcome_permutation(df, h2_delta_rmse)
    reversed_tbl = r1.build_reversed_table()
    nc3 = r1.nc3_time_reversal(reversed_tbl)

    # IMPLEMENTATION COMPLETION (disclosed): H2's single frozen raw p-value
    # for the Holm family is the MORE CONSERVATIVE (larger) of NC1's and
    # NC2's empirical p-values -- both are valid nulls for the same claim
    # per docs/HYPOTHESIS_PROTOCOL.md Sec.9; taking the max is a symmetric,
    # non-cherry-picking rule fixed before comparing the two numbers.
    h2_raw_p = max(nc1["empirical_one_sided_p"], nc2["empirical_one_sided_p"])
    raw_p["H2"] = h2_raw_p

    # ---- Holm correction (Task 7) ----
    holm = r1.holm_correction(raw_p)

    # ---- H1 verdicts ----
    h1_verdicts = {}
    for i, metric in enumerate(CONSTRAINT_COLS):
        key = f"H1-{'ABC'[i]}"
        info = h1[metric]
        adj_p = holm[key]
        if adj_p < r1.ALPHA and info["direction_matches_frozen_prediction"]:
            verdict = "SUPPORTED"
        elif adj_p < r1.ALPHA and not info["direction_matches_frozen_prediction"]:
            verdict = "DIRECTIONALLY OPPOSITE"
        else:
            verdict = "NOT SUPPORTED"
        h1_verdicts[metric] = verdict

    # ---- H2 verdict ----
    h2_adj_p = holm["H2"]
    h2_verdict = "SUPPORTED" if (h2_delta_rmse > 0 and h2_adj_p < r1.ALPHA) else "NOT SUPPORTED"

    overall_verdict = determine_verdict(h1_verdicts, h2_verdict, h2_delta_rmse)

    # ---- H3 ----
    h3 = r1.run_h3(df)

    # ---- descriptive benchmarks ----
    cv_of_cvs = r1.descriptive_cv_of_cvs()
    taylor = r1.descriptive_taylors_law()

    # =====================================================================
    # write result files
    # =====================================================================
    primary = {
        "frozen_protocol_commit": FROZEN_COMMIT,
        "n_series": n, "n_studies": int(n_studies),
        "H1": {("H1-" + "ABC"[i]): {**h1[m], "raw_p_value": raw_p[f"H1-{'ABC'[i]}"],
                                     "holm_adjusted_p": holm[f"H1-{'ABC'[i]}"],
                                     "verdict": h1_verdicts[m]}
               for i, m in enumerate(CONSTRAINT_COLS)},
        "H2": {**h2, "raw_p_value": h2_raw_p, "holm_adjusted_p": h2_adj_p, "verdict": h2_verdict},
        "holm_family": raw_p, "holm_adjusted": holm,
        "overall_verdict": overall_verdict,
    }
    with open("results/round1_primary_results.json", "w") as f:
        json.dump(primary, f, indent=2, default=str)
    write_primary_md(primary)

    nc = {"NC1_within_study_constraint_permutation": nc1,
          "NC2_within_study_outcome_permutation": nc2,
          "NC3_time_reversal_diagnostic": nc3}
    with open("results/round1_negative_controls.json", "w") as f:
        json.dump(nc, f, indent=2, default=str)
    write_nc_md(nc)

    with open("results/round1_stratum_results.json", "w") as f:
        json.dump(h3, f, indent=2, default=str)
    write_stratum_md(h3)

    write_verdict_md(primary, cv_of_cvs, taylor)

    print("OVERALL VERDICT:", overall_verdict)
    print("H1:", h1_verdicts)
    print("H2:", h2_verdict, "delta_rmse=", h2_delta_rmse, "holm_p=", h2_adj_p)


def write_primary_md(p):
    lines = [
        f"FROZEN PROTOCOL COMMIT: {p['frozen_protocol_commit']}",
        "",
        "# Round 1 primary results",
        "",
        "The protocol above was frozen (docs/HYPOTHESIS_PROTOCOL.md) before "
        "this primary hypothesis execution. Sample: "
        f"**{p['n_series']} eligible series across {p['n_studies']} studies** "
        "(3 of the frozen 1,129 eligible series excluded for an undefined "
        "constraint metric -- disclosed in `src/round1_execute.py`, "
        "`common_table()`).",
        "",
        "## H1",
        "",
        "| metric | coef (std.) | 95% CI | raw p | Holm p | direction matches | verdict |",
        "|---|---:|---|---:|---:|---|---|",
    ]
    for i, key in enumerate(["H1-A", "H1-B", "H1-C"]):
        h = p["H1"][key]
        lines.append(
            f"| {key} ({['D3/1','D4/1','Q90/50'][i]}) | {h['coefficient_standardized']:.5f} | "
            f"[{h['ci_95'][0]:.5f}, {h['ci_95'][1]:.5f}] | {h['raw_p_value']:.4f} | "
            f"{h['holm_adjusted_p']:.4f} | {h['direction_matches_frozen_prediction']} | **{h['verdict']}** |"
        )
    h2 = p["H2"]
    lines += [
        "",
        "## H2",
        "",
        f"- M0 pooled out-of-fold RMSE: {h2['M0_pooled_oof_rmse']:.6f}",
        f"- M1 pooled out-of-fold RMSE: {h2['M1_pooled_oof_rmse']:.6f}",
        f"- delta RMSE (M0 - M1, positive = improvement): {h2['delta_rmse_M0_minus_M1']:.6f}",
        f"- M0 pooled out-of-fold R2: {h2['M0_pooled_oof_r2']:.5f}",
        f"- M1 pooled out-of-fold R2: {h2['M1_pooled_oof_r2']:.5f}",
        f"- delta R2 (M1 - M0): {h2['delta_r2_M1_minus_M0']:.5f}",
        f"- folds favoring M1: {h2['n_folds_favoring_M1']} / {h2['n_folds']}",
        f"- median fold delta RMSE: {h2['median_fold_delta_rmse']:.6f}",
        f"- raw p (max of NC1/NC2 empirical p, see docs note): {h2['raw_p_value']:.4f}",
        f"- Holm-adjusted p: {h2['holm_adjusted_p']:.4f}",
        f"- **H2 verdict: {h2['verdict']}**",
        "",
        "### Fold-by-fold RMSE",
        "",
        "| fold | RMSE M0 | RMSE M1 | delta |",
        "|---:|---:|---:|---:|",
    ]
    for i, (a, b, d) in enumerate(zip(h2["fold_rmse_M0"], h2["fold_rmse_M1"], h2["fold_delta_rmse"])):
        lines.append(f"| {i} | {a:.5f} | {b:.5f} | {d:.5f} |")
    lines += [
        "",
        "## Holm family (Task 7)",
        "",
        "| test | raw p | Holm-adjusted p |",
        "|---|---:|---:|",
    ]
    for k in ["H1-A", "H1-B", "H1-C", "H2"]:
        lines.append(f"| {k} | {p['holm_family'][k]:.4f} | {p['holm_adjusted'][k]:.4f} |")
    lines += ["", f"# OVERALL PRIMARY VERDICT: **{p['overall_verdict']}**"]
    with open("results/ROUND1_PRIMARY_RESULTS.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_nc_md(nc):
    lines = [f"FROZEN PROTOCOL COMMIT: {FROZEN_COMMIT}", "", "# Round 1 negative controls", ""]
    for name, d in nc.items():
        lines.append(f"## {name}")
        lines.append("")
        for k, v in d.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    with open("results/ROUND1_NEGATIVE_CONTROLS.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_stratum_md(h3):
    lines = [f"FROZEN PROTOCOL COMMIT: {FROZEN_COMMIT}", "", "# Round 1 H3 stratum results (SECONDARY)", "",
             "Only strata passing the frozen Task 14 adequacy gate are tested "
             "(Air, Water, Herb layer, Soil surface). Trees and Underground are "
             "excluded, not tested. H3 is secondary regardless of outcome and "
             "is never promoted to the primary conclusion.", ""]
    for stratum, d in h3["per_stratum"].items():
        lines.append(f"## {stratum}")
        lines.append(f"- n series: {d['n_series']}, n studies: {d['n_studies']}, CV folds used: {d['cv_n_splits_used']}")
        lines.append(f"- M0 RMSE {d['M0_rmse']:.5f}, M1 RMSE {d['M1_rmse']:.5f}, delta {d['delta_rmse']:.5f}")
        for m, e in d["metric_effects"].items():
            lines.append(f"  - {m}: coef={e['coefficient_standardized']:.4f}, raw p={e['raw_p_value']:.4f}, "
                         f"cluster-robust SE used={e['cluster_robust_se_used']}, direction matches H1={e['matches_frozen_H1_direction']}")
        lines.append("")
    lines.append("## Direction consistency across strata (per metric)")
    for m, info in h3["direction_consistency_across_strata"].items():
        lines.append(f"- {m}: {info['signs_by_stratum']} -> all same sign: {info['all_same_sign']}")
    with open("results/ROUND1_STRATUM_RESULTS.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_verdict_md(primary, cv_of_cvs, taylor):
    lines = [
        f"FROZEN PROTOCOL COMMIT: {FROZEN_COMMIT}",
        "",
        "# Round 1 verdict",
        "",
        "The protocol above was frozen before this primary hypothesis "
        "execution (docs/HYPOTHESIS_PROTOCOL.md, commit 21e6992).",
        "",
        f"## H1 verdicts",
        "",
    ]
    for i, key in enumerate(["H1-A", "H1-B", "H1-C"]):
        lines.append(f"- {key} ({['D3/1','D4/1','Q90/50'][i]}): **{primary['H1'][key]['verdict']}**")
    lines += [
        "",
        f"## H2 verdict: **{primary['H2']['verdict']}**",
        "",
        f"## OVERALL PRIMARY VERDICT: **{primary['overall_verdict']}**",
        "",
        "The manuscript's central title claim (\"Variance Constraints, Not "
        "Variance Magnitude, as Indicators of Insect Community "
        "Vulnerability\") is evaluated strictly against the H2 incremental "
        "out-of-sample criterion above, per Task 8's explicit instruction "
        "that a significant individual H1 coefficient alone is "
        "insufficient.",
        "",
        "## Descriptive benchmarks (NOT evidence for H1/H2)",
        "",
        f"- CV-of-CVs: {cv_of_cvs['cv_of_cvs']:.4f} (n={cv_of_cvs['n_series']}) -- "
        "finite empirical dispersion != ecological upper bound "
        "(`docs/CV_OF_CV_INTERPRETATION.md`)",
        f"- Taylor's Law: b={taylor['taylor_b_slope']:.4f}, R2={taylor['r_squared']:.4f} "
        f"(n={taylor['n_series_used']}) vs. manuscript's reported "
        f"b~{taylor['manuscript_reported_b']}, R2~{taylor['manuscript_reported_r2']} -- "
        "descriptive replication only, kept analytically separate from H1/H2.",
    ]
    with open("results/ROUND1_VERDICT.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    with open("results/round1_descriptive_benchmarks.json", "w") as f:
        json.dump({"cv_of_cvs": cv_of_cvs, "taylors_law": taylor}, f, indent=2, default=str)


if __name__ == "__main__":
    main()
