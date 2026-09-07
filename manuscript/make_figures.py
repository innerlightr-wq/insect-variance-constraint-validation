#!/usr/bin/env python3
"""
Generates manuscript figures EXCLUSIVELY from already-archived, already-
committed results JSON files (results/round1_primary_results.json,
results/h4_permutation_results.json). No new scientific analysis is run
here -- this is a visualization of existing archived outputs only, per
the revision task's explicit instruction (Task 25).
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.dirname(os.path.abspath(__file__)) + "/figures"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.size": 10, "figure.dpi": 150})


def fig1_round1_folds():
    with open(os.path.join(ROOT, "results", "round1_primary_results.json")) as f:
        d = json.load(f)
    rmse0 = d["H2"]["fold_rmse_M0"]
    rmse1 = d["H2"]["fold_rmse_M1"]
    n = len(rmse0)
    x = np.arange(n)
    fig, ax = plt.subplots(figsize=(6, 3.2))
    w = 0.38
    ax.bar(x - w / 2, rmse0, width=w, label="M0 (baseline)", color="#4C72B0")
    ax.bar(x + w / 2, rmse1, width=w, label="M1 (baseline + D3/1, D4/1, Q90/50)", color="#DD8452")
    ax.set_xlabel("Round 1 GroupKFold fold (grouped by DataSource\\_ID)")
    ax.set_ylabel("out-of-fold RMSE")
    ax.set_xticks(x)
    ax.set_title("Round 1: fold-level M0 vs. M1 out-of-fold RMSE (n=10 folds)")
    ax.set_ylim(0, max(max(rmse0), max(rmse1)) * 1.35)
    ax.legend(fontsize=8, loc="upper center", ncol=1, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "round1_fold_rmse.pdf"))
    plt.close(fig)


def fig2_h4_permutation_null():
    with open(os.path.join(ROOT, "results", "h4_permutation_results.json")) as f:
        d = json.load(f)
    sample = np.array(d["null_deltas_sample"])
    observed = d["observed_delta_rmse"]
    s = d["null_deltas_summary"]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.hist(sample, bins=25, color="#8C8C8C", edgecolor="white",
            label=f"reproducible 200-draw sample of the frozen\n10,000-permutation null (seed 20260907)")
    ax.axvline(observed, color="#C44E52", linewidth=2,
               label=f"observed $\\Delta$RMSE = {observed:.5f}")
    ax.axvline(s["q50"], color="black", linestyle=":", linewidth=1, label=f"null median = {s['q50']:.5f}")
    ax.set_xlabel(r"$\Delta\mathrm{RMSE} = \mathrm{RMSE}(M_0) - \mathrm{RMSE}(M_1)$")
    ax.set_ylabel("count (of 200-draw sample)")
    ax.set_title(f"H4: observed $\\Delta$RMSE vs. permutation null\n(full 10,000-permutation p = {d['p_value']:.4f}, one-sided)")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "h4_permutation_null.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    fig1_round1_folds()
    fig2_h4_permutation_null()
    print("wrote figures to", OUT)
