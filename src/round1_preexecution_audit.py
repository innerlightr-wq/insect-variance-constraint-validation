#!/usr/bin/env python3
"""
ROUND 1, Task 1 -- pre-execution integrity check. Verifies the frozen
protocol (commit 21e6992) can be faithfully executed against the current
state of the repository and the raw data, before any hypothesis result is
computed. Still no predictor-outcome association is computed here.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from insect_variance_protocol import (  # noqa: E402
    build_yearly_abundance_table, build_eligibility_table, make_group_folds,
    verify_checksum,
)

DATA_DIR = "data/raw/insect_knb"
FROZEN_COMMIT = "21e699228f40bf4585e42d5896a7835de0b21dca"
FROZEN_COMMIT_SHORT = "21e6992"


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def check_git_state() -> dict:
    status = git("status", "--porcelain")
    head = git("rev-parse", "HEAD")
    return {
        "working_tree_clean_at_time_of_this_script_run": status == "",
        "head_commit": head,
        "head_matches_frozen_commit": head == FROZEN_COMMIT,
        "note": "This script is itself a new, uncommitted Round 1 file, so "
                "'clean at time of THIS run' is expected to read false once "
                "Round 1 work has begun -- it is NOT re-checked in the "
                "READY_TO_EXECUTE_ROUND_1 gate below. The load-bearing check "
                "is that HEAD matches the frozen protocol commit (no "
                "unauthorized commits exist on top of the freeze) and that "
                "the tree was clean immediately before any Round 1 file was "
                "written, which was verified manually and separately, prior "
                "to running this script, per Task 1 step 1.",
    }


def check_checksums() -> dict:
    with open("data/provenance.json") as f:
        prov = json.load(f)
    results = {}
    all_ok = True
    for entry in prov["files"]:
        if "md5_reported_by_dataone" not in entry:
            continue
        path = os.path.join(DATA_DIR, entry["entity_name"])
        ok = verify_checksum(path, entry["md5_reported_by_dataone"])
        results[entry["entity_name"]] = ok
        all_ok = all_ok and ok
    return {"all_files_verified": all_ok, "per_file": results}


def check_eligibility() -> dict:
    ab = pd.read_csv(os.path.join(DATA_DIR, "InsectAbundanceBiomassData.csv"), encoding="latin-1")
    abund = ab[ab["MetricAB"] == "abundance"].copy()
    yearly = build_yearly_abundance_table(abund)
    eligibility = build_eligibility_table(yearly)
    eligible = eligibility[eligibility["eligible"]]
    n_eligible = int(eligible.shape[0])
    n_studies = int(eligible["DataSource_ID"].nunique())
    return {
        "n_eligible": n_eligible,
        "n_studies": n_studies,
        "matches_frozen_1129_series": n_eligible == 1129,
        "matches_frozen_99_studies": n_studies == 99,
        "eligibility_table": eligibility,  # kept in-memory for the fold check below, not serialized directly
    }


def check_folds(eligible: pd.DataFrame) -> dict:
    groups = eligible["DataSource_ID"].values
    folds = make_group_folds(groups, n_splits=10)
    n = len(groups)
    test_fold_of_row = np.full(n, -1)
    violations_train_test_overlap = 0
    for fold_i, (train_idx, test_idx) in enumerate(folds):
        train_groups = set(groups[train_idx])
        test_groups = set(groups[test_idx])
        if train_groups & test_groups:
            violations_train_test_overlap += 1
        for i in test_idx:
            test_fold_of_row[i] = fold_i
    each_row_exactly_one_test_fold = bool((test_fold_of_row >= 0).all())
    fold_sizes = [int(len(test_idx)) for _, test_idx in folds]
    min_fold_size = min(fold_sizes)
    fallback_would_trigger = min_fold_size < 20
    return {
        "n_splits": 10,
        "no_study_in_both_train_and_test_any_fold": violations_train_test_overlap == 0,
        "every_eligible_series_in_exactly_one_test_fold": each_row_exactly_one_test_fold,
        "fold_test_sizes": fold_sizes,
        "min_test_fold_size": min_fold_size,
        "min_fold_size_at_least_20": min_fold_size >= 20,
        "fallback_required": fallback_would_trigger,
        "fallback_invoked": False,  # not invoked -- rule only fires if min < 20
    }


def run() -> dict:
    git_state = check_git_state()
    checksum_state = check_checksums()
    elig_state = check_eligibility()
    eligible_table = elig_state.pop("eligibility_table")
    eligible_only = eligible_table[eligible_table["eligible"]]
    fold_state = check_folds(eligible_only)

    all_pass = (
        git_state["head_matches_frozen_commit"]
        and checksum_state["all_files_verified"]
        and elig_state["matches_frozen_1129_series"]
        and elig_state["matches_frozen_99_studies"]
        and fold_state["no_study_in_both_train_and_test_any_fold"]
        and fold_state["every_eligible_series_in_exactly_one_test_fold"]
        and fold_state["min_fold_size_at_least_20"]
        and not fold_state["fallback_required"]
    )

    return {
        "frozen_protocol_commit": FROZEN_COMMIT_SHORT,
        "git_state": git_state,
        "checksum_state": checksum_state,
        "eligibility_state": elig_state,
        "fold_state": fold_state,
        "READY_TO_EXECUTE_ROUND_1": all_pass,
    }


def write_report(result: dict, out_md: str, out_json: str) -> None:
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    g, c, e, fo = result["git_state"], result["checksum_state"], result["eligibility_state"], result["fold_state"]
    lines = [
        "# Round 1 pre-execution integrity audit",
        "",
        f"FROZEN PROTOCOL COMMIT: {result['frozen_protocol_commit']}",
        "",
        "## 1. Git state",
        "- working tree was confirmed clean, and HEAD confirmed at the "
        "frozen commit, manually and separately, BEFORE any Round 1 file "
        "was written (Task 1 step 1-2).",
        f"- working tree clean at the time this script itself ran: "
        f"{g['working_tree_clean_at_time_of_this_script_run']} "
        f"(expected false — this script and its own output are themselves "
        f"new Round 1 files; not part of the readiness gate, see note in JSON)",
        f"- HEAD: {g['head_commit']}",
        f"- HEAD matches frozen commit (no unauthorized commits on top of the freeze): {g['head_matches_frozen_commit']}",
        "",
        "## 2. Checksums (data/provenance.json vs. local files)",
        f"- all files verified: {c['all_files_verified']}",
    ]
    for name, ok in c["per_file"].items():
        lines.append(f"  - {name}: {'OK' if ok else 'MISMATCH'}")
    lines += [
        "",
        "## 3. Eligible population",
        f"- eligible series: {e['n_eligible']} (frozen: 1129) -> match: {e['matches_frozen_1129_series']}",
        f"- eligible studies: {e['n_studies']} (frozen: 99) -> match: {e['matches_frozen_99_studies']}",
        "",
        "## 4. Grouped fold reproduction (10-fold GroupKFold on DataSource_ID)",
        f"- no study split across train/test in any fold: {fo['no_study_in_both_train_and_test_any_fold']}",
        f"- every eligible series in exactly one test fold: {fo['every_eligible_series_in_exactly_one_test_fold']}",
        f"- fold test sizes: {fo['fold_test_sizes']}",
        f"- minimum test fold size: {fo['min_test_fold_size']} (>= 20 required): {fo['min_fold_size_at_least_20']}",
        f"- fallback required: {fo['fallback_required']}",
        f"- fallback invoked: {fo['fallback_invoked']}",
        "",
        f"## READY TO EXECUTE ROUND 1: **{result['READY_TO_EXECUTE_ROUND_1']}**",
    ]
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    result = run()
    write_report(result, "results/ROUND1_PREEXECUTION_AUDIT.md", "results/round1_preexecution_audit.json")
    print("READY_TO_EXECUTE_ROUND_1:", result["READY_TO_EXECUTE_ROUND_1"])
