#!/usr/bin/env python3
"""
ROUND 2A, Task 12 -- machine-checkable no-peeking verification. Scans this
round's own computational source files for forbidden predictor-outcome
association patterns. Also enforced going forward by
tests/test_round2a_cv_of_cv_feasibility.py::test_no_peeking_guard.
"""
from __future__ import annotations

import ast
import json

ROUND2A_SOURCE_FILES = [
    "src/round2a_cv_of_cv_feasibility.py",
    "src/run_round2a.py",
    "src/round2a_precheck.py",
]

# Only real CODE usage (identifiers, attribute access, function calls,
# string subscript keys) is checked -- docstrings, comments, and print()/
# markdown-writing string literals that merely DISCUSS what must not be
# done are not code usage and are deliberately not flagged. This is an
# AST-based check, not a text grep, specifically so this document's own
# compliance prose (e.g. "no outcome value is referenced") does not
# trigger a false positive.
FORBIDDEN_NAMES = {
    "outcome", "corr", "corrcoef", "roc_auc_score", "rmse", "RMSE",
    "r2_score", "R2", "LinearRegression", "OLS", "p_value", "pvalue",
    "raw_p", "holm_correction", "ols_trend_slope",
}
FORBIDDEN_SUBSCRIPT_KEYS = {"outcome", "late_year_min", "late_year_max", "outcome_reversed"}


def scan_file(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    tree = ast.parse(text, filename=path)
    hits = []

    class Visitor(ast.NodeVisitor):
        def visit_Name(self, node):
            if node.id in FORBIDDEN_NAMES:
                hits.append({"kind": "name", "identifier": node.id, "line": node.lineno})
            self.generic_visit(node)

        def visit_Attribute(self, node):
            if node.attr in FORBIDDEN_NAMES:
                hits.append({"kind": "attribute", "identifier": node.attr, "line": node.lineno})
            self.generic_visit(node)

        def visit_Subscript(self, node):
            key = node.slice
            if isinstance(key, ast.Constant) and isinstance(key.value, str) and key.value in FORBIDDEN_SUBSCRIPT_KEYS:
                hits.append({"kind": "subscript_key", "identifier": key.value, "line": node.lineno})
            self.generic_visit(node)

        def visit_Call(self, node):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in FORBIDDEN_NAMES:
                hits.append({"kind": "call", "identifier": name, "line": node.lineno})
            self.generic_visit(node)

    Visitor().visit(tree)
    return hits


def run() -> dict:
    results = {}
    all_clean = True
    for path in ROUND2A_SOURCE_FILES:
        hits = scan_file(path)
        results[path] = hits
        if hits:
            all_clean = False
    return {"files_scanned": ROUND2A_SOURCE_FILES, "forbidden_pattern_hits": results, "NO_PEEKING_CONFIRMED": all_clean}


def write_report(result: dict, out_md: str, out_json: str) -> None:
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)
    lines = [
        "# Round 2A no-peeking verification (Task 12)",
        "",
        "Machine-checked scan of this round's own computational source "
        "files for forbidden predictor-outcome association patterns "
        "(correlation, regression, RMSE/R2 against an outcome, p-values "
        "for a predictive association, Round 1's `outcome` column, and "
        "any late-window trend computation).",
        "",
    ]
    for path, hits in result["forbidden_pattern_hits"].items():
        status = "CLEAN" if not hits else f"{len(hits)} HIT(S) -- SEE BELOW"
        lines.append(f"- `{path}`: {status}")
        for h in hits:
            lines.append(f"    - pattern `{h['pattern']}` at line {h['line']}")
    lines += ["", f"## NO_PEEKING_CONFIRMED: **{result['NO_PEEKING_CONFIRMED']}**"]
    with open(out_md, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    result = run()
    write_report(result, "results/ROUND2A_NO_PEEKING_AUDIT.md", "results/round2a_no_peeking_audit.json")
    print("NO_PEEKING_CONFIRMED:", result["NO_PEEKING_CONFIRMED"])
