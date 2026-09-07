H4 FROZEN PROTOCOL COMMIT: 3e30670
PARENT FEASIBILITY COMMIT: d3246d9

# H4 primary results

H4-eligible studies: **11**. Outcome rows (series contributing an outcome, C_g broadcast per study): **384**.

## C_g descriptive properties

- n: 11
- mean: 0.40231433789722393
- sd: 0.08799927486176583
- median: 0.4030638359229628
- min: 0.2503095072630244
- max: 0.560552399771103
- iqr: [0.3859360027582389, 0.444756240930816]

## LOSO validation (Task 6)

- pooled RMSE M0: 0.141950
- pooled RMSE M1: 0.144303
- pooled delta RMSE (M0-M1, positive favors C_g): **-0.002354**
- folds favoring M1: 7 / 11
- folds favoring M0: 4 / 11
- ties: 0
- median fold delta RMSE: 0.000956

| study | test N | RMSE M0 | RMSE M1 | delta RMSE |
|---|---:|---:|---:|---:|
| 1488 | 88 | 0.16796 | 0.16800 | -0.00004 |
| 1444 | 60 | 0.11909 | 0.11879 | 0.00030 |
| 300 | 51 | 0.04767 | 0.04231 | 0.00537 |
| 1518 | 39 | 0.08926 | 0.09748 | -0.00822 |
| 1476 | 32 | 0.16974 | 0.16871 | 0.00103 |
| 1477 | 30 | 0.11402 | 0.11307 | 0.00096 |
| 1349 | 28 | 0.23759 | 0.23659 | 0.00100 |
| 1267 | 27 | 0.11398 | 0.11244 | 0.00153 |
| 502 | 15 | 0.11300 | 0.17598 | -0.06298 |
| 1266 | 13 | 0.20000 | 0.20022 | -0.00022 |
| 313 | 1 | 0.15022 | 0.12353 | 0.02669 |

## Secondary: standardized C_g coefficient (Task 7 -- cannot rescue a failed primary result)

- coefficient: 0.008748
- cluster-robust SE: 0.011385
- 95% CI: [-0.01356583647573356, 0.031061814188165247]
- raw p (cluster-robust, asymptotic -- secondary only): 0.4423
- sign: positive, matches predicted direction: True
