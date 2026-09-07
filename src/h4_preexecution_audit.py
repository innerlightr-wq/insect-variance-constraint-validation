#!/usr/bin/env python3
"""H4 EXECUTION, Task 1 -- pre-execution integrity check. Prints/saves a
machine-readable summary of the frozen H4 choices before any real
predictor/outcome pair is loaded."""
from __future__ import annotations

import json
import subprocess

COMMITS = {"round0": "21e6992", "round1": "206742f", "round2a": "d3246d9", "h4_freeze": "3e30670"}


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def commit_exists(ref: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", ref], capture_output=True).returncode == 0


def run() -> dict:
    with open("protocols/h4_protocol.json") as f:
        proto = json.load(f)

    status = git("status", "--porcelain")
    head = git("rev-parse", "HEAD")
    diff_vs_freeze = git("diff", COMMITS["h4_freeze"], "--stat", "--",
                          "docs/H4_PROTOCOL.md", "docs/H4_INTERPRETATION_BOUNDARIES.md",
                          "protocols/h4_protocol.json", "src/h4_pipeline.py",
                          "src/h4_no_peeking_guard.py", "tests/test_h4_pipeline.py")

    tests = subprocess.run(["python3", "-m", "pytest", "-q"], capture_output=True, text=True)
    tests_line = tests.stdout.strip().splitlines()[-1] if tests.stdout.strip() else tests.stderr.strip()

    summary = {
        "minimum_constituent_series": proto["minimum_constituent_series"],
        "historical_window_years": proto["historical_window_years"],
        "chronology_design": proto["chronology_design_definition"],
        "predictor": proto["predictor"]["formula"],
        "outcome": proto["future_outcome"]["formula"],
        "outcome_eligibility_filter": proto["future_outcome"]["h4_specific_eligibility_filter"],
        "predicted_direction": proto["predicted_direction"]["sign_on_C_g_coefficient"],
        "M0": proto["baseline_model_M0"],
        "M1": proto["augmented_model_M1"],
        "primary_statistic": proto["primary_statistic"]["formula"],
        "permutation_count": proto["permutation_procedure"]["permutation_count"],
        "seed": proto["permutation_procedure"]["seed"],
        "alpha": proto["alpha"],
        "support_rule": proto["support_rule"],
    }

    result = {
        "commits_exist": {k: commit_exists(v) for k, v in COMMITS.items()},
        "working_tree_clean_before_h4_execution_files": status == "",
        "head_commit": head,
        "h4_protocol_files_match_freeze_commit": diff_vs_freeze == "",
        "test_summary_line": tests_line,
        "tests_pass_106": tests.returncode == 0 and "106 passed" in tests.stdout,
        "frozen_choices_summary": summary,
    }
    result["READY_FOR_H4_EXECUTION"] = (
        all(result["commits_exist"].values())
        and result["h4_protocol_files_match_freeze_commit"]
        and result["tests_pass_106"]
    )
    return result


def write_report(result: dict, out_md: str, out_json: str) -> None:
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)
    s = result["frozen_choices_summary"]
    lines = [
        "H4 FROZEN PROTOCOL COMMIT: 3e30670",
        "PARENT FEASIBILITY COMMIT: d3246d9",
        "",
        "# H4 pre-execution integrity audit",
        "",
        f"- commits exist: {result['commits_exist']}",
        f"- HEAD: {result['head_commit']}",
        f"- H4 protocol files match freeze commit 3e30670 (zero diff): {result['h4_protocol_files_match_freeze_commit']}",
        f"- tests: {result['test_summary_line']} (expected 106 passed): {result['tests_pass_106']}",
        "",
        "## Frozen H4 choices (machine-readable summary, protocols/h4_protocol.json)",
        "",
        f"- minimum constituent series: {s['minimum_constituent_series']}",
        f"- historical window: {s['historical_window_years']} years -- {s['chronology_design']}",
        f"- predictor: {s['predictor']}",
        f"- outcome: {s['outcome']}",
        f"- outcome eligibility filter: {s['outcome_eligibility_filter']}",
        f"- predicted direction: {s['predicted_direction']}",
        f"- M0: {s['M0']}",
        f"- M1: {s['M1']}",
        f"- primary statistic: {s['primary_statistic']}",
        f"- permutation count: {s['permutation_count']}, seed: {s['seed']}",
        f"- alpha: {s['alpha']}",
        f"- support rule: {json.dumps(s['support_rule'], indent=2)}",
        "",
        f"## READY_FOR_H4_EXECUTION: **{result['READY_FOR_H4_EXECUTION']}**",
    ]
    with open(out_md, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    result = run()
    write_report(result, "results/H4_PREEXECUTION_AUDIT.md", "results/h4_preexecution_audit.json")
    print("READY_FOR_H4_EXECUTION:", result["READY_FOR_H4_EXECUTION"])
