FROZEN PROTOCOL COMMITS REFERENCED (not altered): 21e6992, 206742f

# Round 2A feasibility gate (Task 13)

**No predictor-outcome association was computed anywhere in this round**
(`results/ROUND2A_NO_PEEKING_AUDIT.md`, `NO_PEEKING_CONFIRMED: true`,
AST-verified). The verdict below is based only on: independent study
support, contemporaneous multi-series support, temporal overlap,
estimator stability, chronological separation feasibility, and
pseudoreplication constraints.

## Evidence summary

| audit | key finding |
|---|---|
| Study support (Task 3) | 99 studies have >=1 Round-1-eligible series; only **38** have >=5, **20** have >=15, **10** have >=30. |
| Contemporaneous overlap (Task 4) | 38 studies sustain >=5 contemporaneous eligible series across multiple years; 37 sustain a run of >=5 consecutive such years. At the stricter >=15-series threshold (see estimator stability below), only **19** studies ever achieve it. |
| Window feasibility (Task 5) | At a 10-year window and >=20-series threshold: 34 non-overlapping windows, 197 rolling windows exist corpus-wide — real but concentrated in a minority of studies. |
| Estimator stability (Task 6) | Never undefined/near-zero-denominator at any tested group size, but 95% CI width remains >=0.49 even at n=30, and a single extreme constituent CV still shifts the group estimate by ~0.33 on average at n=30 — **n<15 is not numerically defensible; n>=15-20 is the earliest point CI width and extreme-sensitivity meaningfully improve, and even then the effect is not small.** |
| LEVEL feasibility (Task 8) | 38/99 studies have >=1 adequate 10-year window at the round's working >=5-series bar; this drops to **~19-20 studies** under the stricter, estimator-motivated >=15-series bar. |
| CHANGE feasibility (Task 8) | Only 14/99 studies have >=3 sequential adequate windows, 4 at >=4, 3 at >=5 — **CHANGE is not adequately supported at any reasonable multiplicity.** |
| Chronology (Task 10) | A fixed 10-year-history-plus-held-out-later design retains 35 studies with a full median 10 future years available, zero leakage by construction. |
| Heterogeneity (Task 11) | Meeting the contemporaneous-support threshold is strongly associated with a study's own plot count (median 17.5 vs. 2 plots) — **estimability is confounded with study design scale, not necessarily with anything ecological.** |
| Pseudoreplication (Task 9) | The only defensible inferential unit is the (study, historical-window) pair; **effective N for any claim about the predictor's own explanatory power is the number of adequate study-windows (~19-38, not the ~1,000+ series or plots that would be broadcast onto them).** |

## Verdict

# **MARGINALLY READY** — for a LEVEL-only H4, restricted to studies meeting a stricter (>=15-series) adequacy bar than this round's exploratory >=5 threshold.

**CHANGE is UNDERPOWERED** on its own (3-14 studies depending on the
multiplicity chosen) and must not be part of any primary H4 family.

This is not a READY verdict: an effective cluster count in the high
teens to high thirties is thin for reliable cluster-robust inference by
ordinary econometric convention, the estimator's own extreme-value
sensitivity does not disappear even at the largest feasible group sizes,
and estimability is confounded with a study-design artifact (plot count)
that any future H4 would need to control for or at least disclose
prominently. It is not UNDERPOWERED or BLOCKED either: unlike a case with
single-digit clusters or a mathematically undefined statistic, this round
found real, if thin, structural support for a single, tightly-scoped
LEVEL test.

## Recommended single H4 design (NOT executed, feasibility-driven only)

| element | recommendation | basis |
|---|---|---|
| Inferential unit | (`DataSource_ID`, one historical window) | Task 9 |
| Context grouping | `DataSource_ID` (study) — not a finer stratum-nested context | Task 9; finer grouping's own support was not separately audited and should not be assumed adequate |
| Minimum series per meta-window | **>=15** (stricter than this round's exploratory >=5 bar) | Task 6 — below 15, CI width and single-value sensitivity are at their worst |
| Historical window length | **10 years** | matches Round 1's own `MIN_TOTAL_POINTS` convention; Task 5 shows adequate window counts at this length |
| LEVEL vs. CHANGE | **LEVEL only**, as the sole primary sub-test | Task 8 — CHANGE is underpowered at any threshold |
| Chronological split | **Design C**: fixed 10-year history window, then a fully held-out later period (not a fractional 50/50 or 60/40 split) | Task 10 — retains the most studies with a clean, full future window and zero leakage by construction |
| Minimum valid historical windows required | **1** (LEVEL needs only one adequate window; no CHANGE requirement) | Task 8 |
| Overlapping windows | **Not used** — exactly one, non-overlapping historical window per study, by design | Task 9's independence concerns |
| Treatment of zeros | unchanged from the already-frozen `aggregate_within_year` (sum, `min_count=1`) and `coefficient_of_variation` (`None` if mean=0) rules | Task 7 |
| Raw vs. transformed abundance | **raw** `Number` (matches CV's proven scale invariance) | Task 7 |
| Study grouping/clustering for inference | `DataSource_ID`, but **supplement asymptotic cluster-robust SEs with a permutation-based null** (within- or across-study permutation, mirroring Round 1's NC1/NC2) rather than relying on cluster-robust SEs alone at an effective cluster count this small | Task 9 |
| Minimum adequacy gate | study must have >=15 contemporaneous Round-1-eligible series within its chosen 10-year historical window | Task 6/8 |
| One hypothesis or multiple | **One H4 hypothesis**, tested with both an H1-style individual-coefficient check and an H2-style incremental-out-of-sample-value check against the same conventional baseline used in Round 1 — mirroring Round 1's own dual H1/H2 structure exactly, not introducing a new inferential philosophy | consistency with the already-validated Round 1 design discipline |

**Expected resulting sample, purely from re-applying the numbers already
computed in this round (not a new computation):** approximately 19-20
eligible studies, each contributing one `C_g(t)` LEVEL value and one
(collapsed or per-series, to be decided at freeze time — see Task 9's own
unresolved options 1-3) outcome measure. This is comparable in scale to
several of Round 1's own H3 strata (e.g. Soil surface, 16 studies) — a
legitimate, previously-accepted scale for a secondary/exploratory test in
this project's own established practice, but this document does not
itself decide whether a future H4 should be run as primary or secondary;
that is a freeze-time decision for a separate round.

**This recommendation is not executed. No H4 test is run. No predictor
outcome association exists anywhere in this round's commit.**
