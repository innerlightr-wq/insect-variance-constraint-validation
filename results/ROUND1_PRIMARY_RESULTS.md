FROZEN PROTOCOL COMMIT: 21e6992

# Round 1 primary results

The protocol above was frozen (docs/HYPOTHESIS_PROTOCOL.md) before this primary hypothesis execution. Sample: **1126 eligible series across 99 studies** (3 of the frozen 1,129 eligible series excluded for an undefined constraint metric -- disclosed in `src/round1_execute.py`, `common_table()`).

## H1

| metric | coef (std.) | 95% CI | raw p | Holm p | direction matches | verdict |
|---|---:|---|---:|---:|---|---|
| H1-A (D3/1) | -0.00372 | [-0.06471, 0.05728] | 0.9049 | 1.0000 | False | **NOT SUPPORTED** |
| H1-B (D4/1) | -0.00474 | [-0.06176, 0.05229] | 0.8707 | 1.0000 | False | **NOT SUPPORTED** |
| H1-C (Q90/50) | -0.00897 | [-0.01765, -0.00029] | 0.0427 | 0.1709 | False | **NOT SUPPORTED** |

## H2

- M0 pooled out-of-fold RMSE: 0.168995
- M1 pooled out-of-fold RMSE: 0.169317
- delta RMSE (M0 - M1, positive = improvement): -0.000322
- M0 pooled out-of-fold R2: -0.02926
- M1 pooled out-of-fold R2: -0.03318
- delta R2 (M1 - M0): -0.00393
- folds favoring M1: 4 / 10
- median fold delta RMSE: -0.000457
- raw p (max of NC1/NC2 empirical p, see docs note): 0.5827
- Holm-adjusted p: 1.0000
- **H2 verdict: NOT SUPPORTED**

### Fold-by-fold RMSE

| fold | RMSE M0 | RMSE M1 | delta |
|---:|---:|---:|---:|
| 0 | 0.20518 | 0.20564 | -0.00046 |
| 1 | 0.12819 | 0.12865 | -0.00046 |
| 2 | 0.14255 | 0.14198 | 0.00057 |
| 3 | 0.17162 | 0.17252 | -0.00090 |
| 4 | 0.12587 | 0.12577 | 0.00010 |
| 5 | 0.13594 | 0.13564 | 0.00029 |
| 6 | 0.19601 | 0.19678 | -0.00077 |
| 7 | 0.12456 | 0.12527 | -0.00070 |
| 8 | 0.23997 | 0.23983 | 0.00014 |
| 9 | 0.16977 | 0.17064 | -0.00087 |

## Holm family (Task 7)

| test | raw p | Holm-adjusted p |
|---|---:|---:|
| H1-A | 0.9049 | 1.0000 |
| H1-B | 0.8707 | 1.0000 |
| H1-C | 0.0427 | 0.1709 |
| H2 | 0.5827 | 1.0000 |

# OVERALL PRIMARY VERDICT: **NEGATIVE UPDATE**
