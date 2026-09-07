#!/usr/bin/env python3
"""
ROUND 2A, Task 1 -- repository integrity precheck before the CV-of-CVs
early-warning feasibility audit. Verifies Round 0 (21e6992) and Round 1
(206742f) commits exist, no frozen files are modified, and the baseline
test suite still passes. No predictor-outcome association is computed.
"""
from __future__ import annotations

import json
import subprocess

ROUND0_COMMIT = "21e6992"
ROUND1_COMMIT = "206742f"

FROZEN_PATHS = [
    "docs/HYPOTHESIS_PROTOCOL.md", "docs/ANALYSIS_UNIT.md", "docs/METRIC_PROPERTIES.md",
    "docs/CV_OF_CV_INTERPRETATION.md", "docs/DATA_PROVENANCE.md", "docs/SCOPE_AND_FUTURE_WORK.md",
    "src/insect_variance_protocol.py", "src/audit_dataset.py", "src/power_adequacy_audit.py",
    "src/round1_pipeline.py", "src/round1_execute.py", "src/run_round1.py", "src/round1_preexecution_audit.py",
    "results/DATA_ADEQUACY_AUDIT.md", "results/POWER_ADEQUACY_AUDIT.md",
    "results/ROUND1_PREEXECUTION_AUDIT.md", "results/ROUND1_PRIMARY_RESULTS.md",
    "results/ROUND1_NEGATIVE_CONTROLS.md", "results/ROUND1_STRATUM_RESULTS.md",
    "results/ROUND1_VERDICT.md", "docs/MANUSCRIPT_CLAIM_AUDIT.md",
]


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def commit_exists(ref: str) -> bool:
    r = subprocess.run(["git", "cat-file", "-e", ref], capture_output=True)
    return r.returncode == 0


def run() -> dict:
    status = git("status", "--porcelain")
    head = git("rev-parse", "HEAD")
    diff_stat = git("diff", "--stat", "HEAD", "--", *FROZEN_PATHS)
    tests = subprocess.run(["python3", "-m", "pytest", "-q"], capture_output=True, text=True)
    tests_tail = tests.stdout.strip().splitlines()[-1] if tests.stdout.strip() else tests.stderr.strip()

    result = {
        "round0_commit_exists": commit_exists(ROUND0_COMMIT),
        "round1_commit_exists": commit_exists(ROUND1_COMMIT),
        "working_tree_clean_before_round2a_files": status == "",
        "head_commit": head,
        "frozen_paths_zero_diff": diff_stat == "",
        "frozen_paths_diff_output": diff_stat,
        "test_run_summary_line": tests_tail,
        "test_run_returncode": tests.returncode,
        "tests_pass": tests.returncode == 0 and "63 passed" in tests.stdout,
    }
    result["INTEGRITY_OK"] = (
        result["round0_commit_exists"] and result["round1_commit_exists"]
        and result["frozen_paths_zero_diff"] and result["tests_pass"]
    )
    return result


def write_report(result: dict, out_md: str, out_json: str) -> None:
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)
    lines = [
        "# Round 2A pre-check: repository integrity",
        "",
        f"- Round 0 commit ({ROUND0_COMMIT}) exists: {result['round0_commit_exists']}",
        f"- Round 1 commit ({ROUND1_COMMIT}) exists: {result['round1_commit_exists']}",
        f"- working tree clean before any Round 2A file was written: "
        f"{result['working_tree_clean_before_round2a_files']}",
        f"- HEAD: {result['head_commit']}",
        f"- frozen Round 0/Round 1 files show zero diff: {result['frozen_paths_zero_diff']}",
        f"- test suite: {result['test_run_summary_line']}",
        f"- tests pass (63 passed, matches baseline): {result['tests_pass']}",
        "",
        f"## INTEGRITY_OK: **{result['INTEGRITY_OK']}**",
    ]
    with open(out_md, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    result = run()
    write_report(result, "results/ROUND2A_PRECHECK.md", "results/round2a_precheck.json")
    print("INTEGRITY_OK:", result["INTEGRITY_OK"])
