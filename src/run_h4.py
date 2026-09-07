#!/usr/bin/env python3
"""
H4 EXECUTION -- runs the frozen protocol (docs/H4_PROTOCOL.md, commit
3e30670) exactly once against the real corpus. Every choice below is
copied from protocols/h4_protocol.json and src/h4_pipeline.py, unchanged.
No alternate specification is computed anywhere in this script.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h4_pipeline as h4  # noqa: E402
from insect_variance_protocol import build_yearly_abundance_table, build_eligibility_table  # noqa: E402
from round1_pipeline import build_modeling_table, BASELINE_COLS  # noqa: E402
from round1_execute import pooled_rmse  # noqa: E402

H4_FREEZE_COMMIT = "3e30670"
PARENT_FEASIBILITY_COMMIT = "d3246d9"


# =============================================================================
# TASK 2 -- materialize H4 population
# =============================================================================
def materialize_population():
    ab = pd.read_csv("data/raw/insect_knb/InsectAbundanceBiomassData.csv", encoding="latin-1")
    abund = ab[ab["MetricAB"] == "abundance"].copy()
    yearly = build_yearly_abundance_table(abund)
    eligibility = build_eligibility_table(yearly)
    eligible = eligibility[eligibility["eligible"]]
    usable = yearly.dropna(subset=["Number"])
    eligible_keys = list(map(tuple, eligible[["DataSource_ID", "Plot_ID", "Stratum"]].values))

    candidate_studies = sorted(eligible["DataSource_ID"].unique())

    round1_table = build_modeling_table()  # Round 1's own, unchanged, frozen per-series table
    round1_by_key = {
        (r["DataSource_ID"], r["Plot_ID"], r["Stratum"]): r for _, r in round1_table.iterrows()
    }

    study_reports = {}
    adequate_studies = {}
    for study_id in candidate_studies:
        adequacy = h4.study_h4_adequate(usable, eligible_keys, study_id)
        if not adequacy["adequate"]:
            study_reports[study_id] = {"adequate": False, "reason": adequacy["reason"]}
            continue
        window = adequacy["window"]
        constituents = adequacy["constituent_keys"]

        # outcome-contributing series: constituent AND passes the frozen
        # H4-specific timing filter against THIS series' own Round-1 late window
        outcome_rows = []
        for k in constituents:
            r1 = round1_by_key.get(k)
            if r1 is None:
                continue  # constituent membership only requires >=2 obs in hist_years;
                          # it need not be a Round-1-*eligible* series in the >=10-year sense... but
                          # constituents are drawn from eligible_keys, so this branch is never hit.
            if h4.series_outcome_eligible(int(r1["late_year_min"]), window["hist_years"]):
                outcome_rows.append(k)

        study_reports[study_id] = {
            "adequate": True,
            "n_constituent_series": len(constituents),
            "hist_years": window["hist_years"],
            "fut_years": window["fut_years"],
            "n_outcome_contributing_series": len(outcome_rows),
        }
        if len(outcome_rows) >= 1:
            adequate_studies[study_id] = {
                "window": window, "constituents": constituents, "outcome_keys": outcome_rows,
            }

    return {
        "usable": usable, "eligible_keys": eligible_keys, "round1_table": round1_table,
        "round1_by_key": round1_by_key, "candidate_studies": candidate_studies,
        "study_reports": study_reports, "adequate_studies": adequate_studies,
    }


# =============================================================================
# TASK 3 -- compute frozen C_g for every adequate study-window
# =============================================================================
def compute_all_cg(usable, adequate_studies) -> dict:
    cg_by_study = {}
    for study_id, info in adequate_studies.items():
        cg = h4.compute_C_g(usable, info["constituents"], info["window"]["hist_years"])
        if cg is not None:
            cg_by_study[study_id] = cg
    return cg_by_study


# =============================================================================
# TASK 4 -- leakage audit
# =============================================================================
def leakage_audit(adequate_studies: dict, round1_by_key: dict) -> dict:
    violations = []
    checks = 0
    for study_id, info in adequate_studies.items():
        hist_max = max(info["window"]["hist_years"])
        for k in info["outcome_keys"]:
            r1 = round1_by_key[k]
            checks += 1
            if not (hist_max < int(r1["late_year_min"])):
                violations.append({"study": study_id, "series": k, "hist_max": hist_max,
                                    "outcome_late_year_min": int(r1["late_year_min"])})
    return {"n_checks": checks, "n_violations": len(violations), "violations": violations,
            "LEAKAGE_FREE": len(violations) == 0}


# =============================================================================
# TASK 2/5 -- build the H4 analysis table (one row per outcome-contributing series)
# =============================================================================
def build_h4_table(adequate_studies: dict, cg_by_study: dict, round1_by_key: dict) -> pd.DataFrame:
    rows = []
    for study_id, info in adequate_studies.items():
        if study_id not in cg_by_study:
            continue
        cg = cg_by_study[study_id]
        for k in info["outcome_keys"]:
            r1 = round1_by_key[k]
            baseline_row = {c: r1[c] for c in BASELINE_COLS}
            rows.append(h4.build_h4_row(study_id, cg, baseline_row, float(r1["outcome"])))
    df = pd.DataFrame(rows)
    return df.dropna(subset=BASELINE_COLS + ["C_g", "outcome"]).reset_index(drop=True)


# =============================================================================
# TASK 6/7 -- LOSO validation, observed statistics
# =============================================================================
def run_loso(df: pd.DataFrame):
    y = df["outcome"].values.astype(float)
    groups = df["DataSource_ID"].values
    X0 = df[BASELINE_COLS].values.astype(float)
    X1 = df[BASELINE_COLS + ["C_g"]].values.astype(float)

    folds = h4.loso_folds(groups)
    fold_records = []
    oof0 = np.full(len(y), np.nan)
    oof1 = np.full(len(y), np.nan)
    for train_idx, test_idx in folds:
        study_id = groups[test_idx][0]
        preds0, _ = h4._fit_predict_fold(X0[train_idx], y[train_idx], X0[test_idx])
        preds1, _ = h4._fit_predict_fold(X1[train_idx], y[train_idx], X1[test_idx])
        oof0[test_idx] = preds0
        oof1[test_idx] = preds1
        rmse0 = float(np.sqrt(np.mean((preds0 - y[test_idx]) ** 2)))
        rmse1 = float(np.sqrt(np.mean((preds1 - y[test_idx]) ** 2)))
        fold_records.append({
            "DataSource_ID": str(study_id), "test_n": int(len(test_idx)),
            "rmse_M0": rmse0, "rmse_M1": rmse1, "delta_rmse": rmse0 - rmse1,
        })

    rmse0_pooled = pooled_rmse(y, oof0)
    rmse1_pooled = pooled_rmse(y, oof1)
    delta_pooled = rmse0_pooled - rmse1_pooled

    n_favor_m1 = sum(1 for r in fold_records if r["delta_rmse"] > 0)
    n_favor_m0 = sum(1 for r in fold_records if r["delta_rmse"] < 0)
    n_ties = sum(1 for r in fold_records if r["delta_rmse"] == 0)
    median_fold_delta = float(np.median([r["delta_rmse"] for r in fold_records]))

    return {
        "fold_records": fold_records, "rmse_M0_pooled": rmse0_pooled, "rmse_M1_pooled": rmse1_pooled,
        "delta_rmse_pooled": delta_pooled, "n_folds_favoring_M1": n_favor_m1,
        "n_folds_favoring_M0": n_favor_m0, "n_ties": n_ties, "median_fold_delta_rmse": median_fold_delta,
        "n_folds": len(fold_records),
    }


def secondary_coefficient(df: pd.DataFrame) -> dict:
    X = df[BASELINE_COLS + ["C_g"]].values.astype(float)
    Xstd = (X - X.mean(axis=0)) / X.std(axis=0, ddof=0)
    y = df["outcome"].values.astype(float)
    groups = df["DataSource_ID"].values
    Xd = sm.add_constant(Xstd)
    model = sm.OLS(y, Xd).fit(cov_type="cluster", cov_kwds={"groups": groups})
    coef_idx = Xd.shape[1] - 1
    coef = float(model.params[coef_idx])
    se = float(model.bse[coef_idx])
    ci = model.conf_int(alpha=h4.ALPHA)[coef_idx]
    p = float(model.pvalues[coef_idx])
    return {"coefficient_standardized": coef, "se_cluster_robust": se,
            "ci_95": [float(ci[0]), float(ci[1])], "raw_p_value_cluster_robust": p,
            "sign": "positive" if coef > 0 else ("negative" if coef < 0 else "zero"),
            "matches_predicted_direction": coef > 0}


# =============================================================================
# TASK 8 -- frozen permutation test
# =============================================================================
def run_permutation_test(df: pd.DataFrame, cg_by_study: dict, observed_delta_rmse: float):
    study_ids = np.array(sorted(cg_by_study.keys()))
    null_deltas = np.empty(h4.PERMUTATION_COUNT)
    y = df["outcome"].values.astype(float)
    groups = df["DataSource_ID"].values
    X0 = df[BASELINE_COLS].values.astype(float)
    rmse0 = h4.fit_and_pool_rmse(X0, y, groups)  # M0 unaffected by any C_g permutation -- computed once

    for b in range(h4.PERMUTATION_COUNT):
        perm_map = h4.permute_study_level_mapping(study_ids, cg_by_study, seed=h4.SEED + b)
        cg_perm_col = df["DataSource_ID"].map(perm_map).values.astype(float)
        X1_perm = np.column_stack([X0, cg_perm_col])
        rmse1_perm = h4.fit_and_pool_rmse(X1_perm, y, groups)
        null_deltas[b] = rmse0 - rmse1_perm

    p_value = h4.permutation_p_value(observed_delta_rmse, null_deltas)
    return {
        "null_deltas_summary": {
            "n": int(len(null_deltas)), "mean": float(null_deltas.mean()), "sd": float(null_deltas.std(ddof=1)),
            "q05": float(np.quantile(null_deltas, 0.05)), "q50": float(np.quantile(null_deltas, 0.50)),
            "q95": float(np.quantile(null_deltas, 0.95)), "min": float(null_deltas.min()), "max": float(null_deltas.max()),
        },
        "count_null_ge_observed": int(np.sum(null_deltas >= observed_delta_rmse)),
        "p_value": p_value,
        "null_deltas_sample": [float(x) for x in null_deltas[:200]],  # reproducible summary, not the full 10000
    }


# =============================================================================
# orchestration
# =============================================================================
def main():
    pop = materialize_population()
    adequate = pop["adequate_studies"]
    study_reports = pop["study_reports"]

    n_candidate = len(pop["candidate_studies"])
    n_structurally_adequate = sum(1 for v in study_reports.values() if v.get("adequate"))
    n_failing = n_candidate - n_structurally_adequate
    n_h4_eligible = len(adequate)

    if n_h4_eligible < h4.MIN_STUDIES_FOR_INTERPRETABLE:
        verdict = "UNINTERPRETABLE / BLOCKED"
        print("VERDICT:", verdict, f"(only {n_h4_eligible} H4-eligible studies, < {h4.MIN_STUDIES_FOR_INTERPRETABLE})")
        write_blocked(n_candidate, n_structurally_adequate, n_failing, n_h4_eligible, study_reports)
        return

    cg_by_study = compute_all_cg(pop["usable"], adequate)
    la = leakage_audit(adequate, pop["round1_by_key"])
    write_leakage(la)
    if not la["LEAKAGE_FREE"]:
        print("LEAKAGE DETECTED -- STOPPING PER PROTOCOL")
        return

    df = build_h4_table(adequate, cg_by_study, pop["round1_by_key"])

    cg_arr = df.groupby("DataSource_ID")["C_g"].first().values
    cg_descriptive = {
        "n": int(len(cg_arr)), "mean": float(np.mean(cg_arr)), "sd": float(np.std(cg_arr, ddof=1)),
        "median": float(np.median(cg_arr)), "min": float(np.min(cg_arr)), "max": float(np.max(cg_arr)),
        "iqr": [float(np.quantile(cg_arr, 0.25)), float(np.quantile(cg_arr, 0.75))],
    }

    loso = run_loso(df)
    sec = secondary_coefficient(df)
    perm = run_permutation_test(df, cg_by_study, loso["delta_rmse_pooled"])
    p_opposite = (1 + (h4.PERMUTATION_COUNT - perm["count_null_ge_observed"])) / (h4.PERMUTATION_COUNT + 1)

    verdict = h4.h4_verdict(n_h4_eligible, delta_rmse=loso["delta_rmse_pooled"],
                             p_value=perm["p_value"], p_value_opposite=p_opposite)

    write_population(n_candidate, n_structurally_adequate, n_failing, n_h4_eligible, study_reports, cg_descriptive)
    write_primary(n_h4_eligible, df, cg_descriptive, loso, sec)
    write_permutation(loso["delta_rmse_pooled"], perm, p_opposite)
    write_verdict(verdict, n_h4_eligible, loso, perm, sec)
    write_synthesis(n_h4_eligible, loso, perm, verdict)

    print("N_H4_ELIGIBLE_STUDIES:", n_h4_eligible)
    print("RMSE M0:", loso["rmse_M0_pooled"], "RMSE M1:", loso["rmse_M1_pooled"])
    print("DELTA_RMSE:", loso["delta_rmse_pooled"])
    print("PERMUTATION_P:", perm["p_value"])
    print("VERDICT:", verdict)


def write_blocked(n_candidate, n_adequate, n_failing, n_h4_eligible, study_reports):
    lines = [
        f"H4 FROZEN PROTOCOL COMMIT: {H4_FREEZE_COMMIT}",
        f"PARENT FEASIBILITY COMMIT: {PARENT_FEASIBILITY_COMMIT}",
        "", "# H4 primary results -- UNINTERPRETABLE / BLOCKED", "",
        f"Candidate studies: {n_candidate}. Structurally adequate (>=15 constituents, window): {n_adequate}. "
        f"Failing: {n_failing}. H4-eligible (>=1 outcome-contributing series): {n_h4_eligible} "
        f"(< frozen minimum of {10}).",
        "", "Per protocol Sec.14, primary inference is not executed.",
    ]
    with open("results/H4_VERDICT.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def _jsonable(obj):
    """Recursively converts numpy scalar keys/values (e.g. int64
    DataSource_ID) to native Python types for json.dump -- serialization
    compatibility only, no scientific content is altered."""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def write_population(n_candidate, n_adequate, n_failing, n_h4_eligible, study_reports, cg_descriptive):
    with open("results/h4_population.json", "w") as f:
        json.dump(_jsonable({"n_candidate_studies": n_candidate, "n_structurally_adequate": n_adequate,
                   "n_failing": n_failing, "n_h4_eligible": n_h4_eligible,
                   "study_reports": study_reports, "cg_descriptive": cg_descriptive}), f, indent=2, default=str)
    lines = [
        f"H4 FROZEN PROTOCOL COMMIT: {H4_FREEZE_COMMIT}",
        f"PARENT FEASIBILITY COMMIT: {PARENT_FEASIBILITY_COMMIT}",
        "", "# H4 population (Task 2)", "",
        f"- candidate studies (Round-1-eligible-bearing): {n_candidate}",
        f"- structurally adequate (>=15 constituent series in the fixed 10-yr window): **{n_adequate}**",
        f"- failing: {n_failing}",
        f"- H4-eligible (adequate window AND >=1 outcome-contributing series): **{n_h4_eligible}**",
        "", "## Per-study detail", "",
        "| study | adequate | constituents | outcome series | hist years | fut years |",
        "|---|---|---:|---:|---|---|",
    ]
    for sid, v in study_reports.items():
        if v.get("adequate"):
            lines.append(f"| {sid} | yes | {v['n_constituent_series']} | {v['n_outcome_contributing_series']} | "
                         f"{v['hist_years'][0]}-{v['hist_years'][-1]} | {v['fut_years'][0]}-{v['fut_years'][-1]} |")
    lines += ["", "## C_g descriptive properties (Task 3, descriptive only, no removal/winsorization/transform)", ""]
    for k, val in cg_descriptive.items():
        lines.append(f"- {k}: {val}")
    with open("results/H4_POPULATION.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_leakage(la):
    with open("results/h4_leakage_audit.json", "w") as f:
        json.dump(_jsonable(la), f, indent=2, default=str)
    lines = [
        f"H4 FROZEN PROTOCOL COMMIT: {H4_FREEZE_COMMIT}",
        f"PARENT FEASIBILITY COMMIT: {PARENT_FEASIBILITY_COMMIT}",
        "", "# H4 leakage audit (Task 4)", "",
        f"- checks performed (one per outcome-contributing series): {la['n_checks']}",
        f"- violations: {la['n_violations']}",
        f"- LEAKAGE_FREE: **{la['LEAKAGE_FREE']}**",
        "", "Check: for every outcome-contributing series, "
        "max(study historical predictor years) < min(that series' own Round-1 future/late years).",
    ]
    with open("results/H4_LEAKAGE_AUDIT.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_primary(n_h4_eligible, df, cg_descriptive, loso, sec):
    payload = {"h4_freeze_commit": H4_FREEZE_COMMIT, "parent_feasibility_commit": PARENT_FEASIBILITY_COMMIT,
               "n_h4_eligible_studies": n_h4_eligible, "n_outcome_rows": int(df.shape[0]),
               "cg_descriptive": cg_descriptive, "loso": {k: v for k, v in loso.items()},
               "secondary_coefficient": sec}
    with open("results/h4_primary_results.json", "w") as f:
        json.dump(_jsonable(payload), f, indent=2, default=str)
    lines = [
        f"H4 FROZEN PROTOCOL COMMIT: {H4_FREEZE_COMMIT}",
        f"PARENT FEASIBILITY COMMIT: {PARENT_FEASIBILITY_COMMIT}",
        "", "# H4 primary results", "",
        f"H4-eligible studies: **{n_h4_eligible}**. Outcome rows (series contributing an outcome, "
        f"C_g broadcast per study): **{df.shape[0]}**.",
        "", "## C_g descriptive properties", "",
    ]
    for k, v in cg_descriptive.items():
        lines.append(f"- {k}: {v}")
    lines += [
        "", "## LOSO validation (Task 6)", "",
        f"- pooled RMSE M0: {loso['rmse_M0_pooled']:.6f}",
        f"- pooled RMSE M1: {loso['rmse_M1_pooled']:.6f}",
        f"- pooled delta RMSE (M0-M1, positive favors C_g): **{loso['delta_rmse_pooled']:.6f}**",
        f"- folds favoring M1: {loso['n_folds_favoring_M1']} / {loso['n_folds']}",
        f"- folds favoring M0: {loso['n_folds_favoring_M0']} / {loso['n_folds']}",
        f"- ties: {loso['n_ties']}",
        f"- median fold delta RMSE: {loso['median_fold_delta_rmse']:.6f}",
        "", "| study | test N | RMSE M0 | RMSE M1 | delta RMSE |", "|---|---:|---:|---:|---:|",
    ]
    for r in loso["fold_records"]:
        lines.append(f"| {r['DataSource_ID']} | {r['test_n']} | {r['rmse_M0']:.5f} | {r['rmse_M1']:.5f} | {r['delta_rmse']:.5f} |")
    lines += [
        "", "## Secondary: standardized C_g coefficient (Task 7 -- cannot rescue a failed primary result)", "",
        f"- coefficient: {sec['coefficient_standardized']:.6f}",
        f"- cluster-robust SE: {sec['se_cluster_robust']:.6f}",
        f"- 95% CI: {sec['ci_95']}",
        f"- raw p (cluster-robust, asymptotic -- secondary only): {sec['raw_p_value_cluster_robust']:.4f}",
        f"- sign: {sec['sign']}, matches predicted direction: {sec['matches_predicted_direction']}",
    ]
    with open("results/H4_PRIMARY_RESULTS.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_permutation(observed_delta, perm, p_opposite):
    payload = {"h4_freeze_commit": H4_FREEZE_COMMIT, "parent_feasibility_commit": PARENT_FEASIBILITY_COMMIT,
               "observed_delta_rmse": observed_delta, **perm, "p_value_opposite_tail": p_opposite}
    with open("results/h4_permutation_results.json", "w") as f:
        json.dump(_jsonable(payload), f, indent=2, default=str)
    s = perm["null_deltas_summary"]
    lines = [
        f"H4 FROZEN PROTOCOL COMMIT: {H4_FREEZE_COMMIT}",
        f"PARENT FEASIBILITY COMMIT: {PARENT_FEASIBILITY_COMMIT}",
        "", "# H4 permutation test (Task 8)", "",
        "10,000 permutations, seed 20260907, between-study permutation of the "
        "study-to-C_g mapping, one-sided.", "",
        f"- observed delta RMSE: {observed_delta:.6f}",
        f"- null mean: {s['mean']:.6f}, null SD: {s['sd']:.6f}",
        f"- null quantiles: q05={s['q05']:.6f}, q50={s['q50']:.6f}, q95={s['q95']:.6f}, "
        f"range=[{s['min']:.6f}, {s['max']:.6f}]",
        f"- count(null >= observed): {perm['count_null_ge_observed']} / 10000",
        f"- **p-value (primary, one-sided, predicted direction): {perm['p_value']:.4f}**",
        f"- p-value (opposite tail, for DIRECTIONALLY OPPOSITE check only): {p_opposite:.4f}",
    ]
    with open("results/H4_PERMUTATION_RESULTS.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_verdict(verdict, n_h4_eligible, loso, perm, sec):
    lines = [
        f"H4 FROZEN PROTOCOL COMMIT: {H4_FREEZE_COMMIT}",
        f"PARENT FEASIBILITY COMMIT: {PARENT_FEASIBILITY_COMMIT}",
        "", "# H4 verdict", "",
        f"Effective study N: {n_h4_eligible}. Delta RMSE: {loso['delta_rmse_pooled']:.6f}. "
        f"Permutation p (one-sided): {perm['p_value']:.4f}.",
        "", f"# H4 VERDICT: **{verdict}**", "",
    ]
    if verdict == "SUPPORTED":
        lines.append("Permitted conclusion: historical contextual LEVEL CV-of-CVs contains prospective "
                     "information about subsequent abundance change under this frozen design. "
                     "Because effective N is approximately 11 studies, this evidence is characterized "
                     "conservatively (docs/H4_INTERPRETATION_BOUNDARIES.md).")
    elif verdict == "DIRECTIONALLY OPPOSITE":
        lines.append("The observed effect is reliably in the direction opposite the frozen prediction. "
                     "Stated plainly, without a post-hoc theory.")
    elif verdict == "UNINTERPRETABLE / BLOCKED":
        lines.append("Fewer than the frozen minimum of 10 H4-eligible studies survived every gate; "
                     "primary inference was not executed.")
    else:
        lines.append("Permitted conclusion: CV-of-CVs remains a contextual descriptive statistic, but "
                     "this prospectively frozen test does not demonstrate incremental early-warning "
                     "value for subsequent abundance change (docs/H4_INTERPRETATION_BOUNDARIES.md).")
    lines.append("")
    lines.append(f"Secondary coefficient (cannot rescue a failed primary result): "
                 f"{sec['coefficient_standardized']:.6f}, sign {sec['sign']}, "
                 f"cluster-robust p={sec['raw_p_value_cluster_robust']:.4f} (asymptotic, secondary only).")
    with open("results/H4_VERDICT.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def write_synthesis(n_h4_eligible, loso, perm, verdict):
    lines = [
        f"H4 FROZEN PROTOCOL COMMIT: {H4_FREEZE_COMMIT}",
        f"PARENT FEASIBILITY COMMIT: {PARENT_FEASIBILITY_COMMIT}",
        "", "# Round 1 / H4 synthesis", "",
        "H4 is scientifically separate from Round 1 -- neither result rewrites the other.", "",
        "| Test | Predictor | Level | Effective N | Prospective? | Primary result | Verdict |",
        "|---|---|---|---:|---|---|---|",
        "| Round 1 H1-A | D3/1 | individual series | 1126 series / 99 studies | yes | Holm p=1.000, wrong direction | NOT SUPPORTED |",
        "| Round 1 H1-B | D4/1 | individual series | 1126 series / 99 studies | yes | Holm p=1.000, wrong direction | NOT SUPPORTED |",
        "| Round 1 H1-C | Q90/50 | individual series | 1126 series / 99 studies | yes | Holm p=0.171, wrong direction | NOT SUPPORTED |",
        "| Round 1 H2 | D3/1+D4/1+Q90/50 | individual series, incremental | 1126 series / 99 studies | yes | delta_rmse=-0.00032, Holm p=1.000 | NOT SUPPORTED |",
        f"| H4 | C_g (study-level CV-of-CVs) | study-context LEVEL | {n_h4_eligible} studies | yes | "
        f"delta_rmse={loso['delta_rmse_pooled']:.5f}, perm p={perm['p_value']:.4f} | {verdict} |",
        "",
        "Round 1's individual-series constraint metrics and H4's study-level "
        "meta-variability predictor are structurally different quantities, tested "
        "under different (though related) frozen designs. Neither result is used "
        "to reinterpret the other.",
    ]
    with open("results/ROUND1_H4_SYNTHESIS.md", "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
