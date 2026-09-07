H4 FROZEN PROTOCOL COMMIT: 3e30670
PARENT FEASIBILITY COMMIT: d3246d9

# Round 1 / H4 synthesis

H4 is scientifically separate from Round 1 -- neither result rewrites the other.

| Test | Predictor | Level | Effective N | Prospective? | Primary result | Verdict |
|---|---|---|---:|---|---|---|
| Round 1 H1-A | D3/1 | individual series | 1126 series / 99 studies | yes | Holm p=1.000, wrong direction | NOT SUPPORTED |
| Round 1 H1-B | D4/1 | individual series | 1126 series / 99 studies | yes | Holm p=1.000, wrong direction | NOT SUPPORTED |
| Round 1 H1-C | Q90/50 | individual series | 1126 series / 99 studies | yes | Holm p=0.171, wrong direction | NOT SUPPORTED |
| Round 1 H2 | D3/1+D4/1+Q90/50 | individual series, incremental | 1126 series / 99 studies | yes | delta_rmse=-0.00032, Holm p=1.000 | NOT SUPPORTED |
| H4 | C_g (study-level CV-of-CVs) | study-context LEVEL | 11 studies | yes | delta_rmse=-0.00235, perm p=0.5304 | NOT SUPPORTED |

Round 1's individual-series constraint metrics and H4's study-level meta-variability predictor are structurally different quantities, tested under different (though related) frozen designs. Neither result is used to reinterpret the other.
