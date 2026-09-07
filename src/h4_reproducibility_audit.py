#!/usr/bin/env python3
"""H4 EXECUTION, Task 15 -- reproducibility audit."""
from __future__ import annotations

import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402


def run() -> dict:
    import run_h4
    import h4_pipeline as h4
    from insect_variance_protocol import verify_checksum

    # 1. data checksums
    with open("data/provenance.json") as f:
        prov = json.load(f)
    checksum_ok = all(
        verify_checksum(os.path.join("data/raw/insect_knb", e["entity_name"]), e["md5_reported_by_dataone"])
        for e in prov["files"] if "md5_reported_by_dataone" in e
    )

    # 2. deterministic population construction
    pop_a = run_h4.materialize_population()
    pop_b = run_h4.materialize_population()
    population_deterministic = pop_a["study_reports"] == pop_b["study_reports"]

    # 3. deterministic C_g
    cg_a = run_h4.compute_all_cg(pop_a["usable"], pop_a["adequate_studies"])
    cg_b = run_h4.compute_all_cg(pop_b["usable"], pop_b["adequate_studies"])
    cg_deterministic = cg_a == cg_b

    # 4. deterministic LOSO folds
    df = run_h4.build_h4_table(pop_a["adequate_studies"], cg_a, pop_a["round1_by_key"])
    groups = df["DataSource_ID"].values
    folds_a = h4.loso_folds(groups)
    folds_b = h4.loso_folds(groups)
    folds_deterministic = all(
        list(ta) == list(tb) for (_, ta), (_, tb) in zip(folds_a, folds_b)
    )

    # 5/6. seed and permutation count, as actually recorded
    with open("results/h4_permutation_results.json") as f:
        perm_recorded = json.load(f)
    seed_correct = h4.SEED == 20260907
    permutation_count_correct = (
        h4.PERMUTATION_COUNT == 10000 and perm_recorded["null_deltas_summary"]["n"] == 10000
    )

    # 7. no future leakage (re-verify from the recorded audit)
    with open("results/h4_leakage_audit.json") as f:
        leakage_recorded = json.load(f)
    leakage_free = leakage_recorded["LEAKAGE_FREE"] is True

    # 8. no alternate specifications executed -- structural source scan
    with open("src/run_h4.py") as f:
        run_h4_src = f.read()
    forbidden_literals = ["window_years = 3", "window_years = 5", "window_years = 7",
                           "MIN_CONSTITUENT_SERIES = 5", "MIN_CONSTITUENT_SERIES = 10",
                           "MIN_CONSTITUENT_SERIES = 20", "MIN_CONSTITUENT_SERIES = 30",
                           "n_splits=10)", "GroupKFold(n_splits=10"]
    no_alternate_specs = not any(lit in run_h4_src for lit in forbidden_literals)

    all_ok = all([
        checksum_ok, population_deterministic, cg_deterministic, folds_deterministic,
        seed_correct, permutation_count_correct, leakage_free, no_alternate_specs,
    ])

    return {
        "data_checksums_verified": checksum_ok,
        "population_construction_deterministic": population_deterministic,
        "C_g_deterministic": cg_deterministic,
        "LOSO_folds_deterministic": folds_deterministic,
        "seed_correct_20260907": seed_correct,
        "permutation_count_correct_10000": permutation_count_correct,
        "no_future_leakage": leakage_free,
        "no_alternate_specifications_in_source": no_alternate_specs,
        "REPRODUCIBILITY_CONFIRMED": all_ok,
    }


def write_report(result: dict, out_md: str) -> None:
    lines = [
        "H4 FROZEN PROTOCOL COMMIT: 3e30670",
        "PARENT FEASIBILITY COMMIT: d3246d9",
        "", "# H4 reproducibility audit (Task 15)", "",
    ]
    for k, v in result.items():
        if k == "REPRODUCIBILITY_CONFIRMED":
            continue
        lines.append(f"- {k}: {v}")
    lines += ["", f"## REPRODUCIBILITY_CONFIRMED: **{result['REPRODUCIBILITY_CONFIRMED']}**"]
    with open(out_md, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    result = run()
    write_report(result, "results/H4_REPRODUCIBILITY_AUDIT.md")
    print("REPRODUCIBILITY_CONFIRMED:", result["REPRODUCIBILITY_CONFIRMED"])
