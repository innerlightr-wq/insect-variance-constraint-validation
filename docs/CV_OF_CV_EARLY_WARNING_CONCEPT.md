# CV-of-CVs as a prospective early-warning concept — feasibility framing

**This document defines a feasibility QUESTION, not a hypothesis test. No
predictor–future-outcome association is computed anywhere in this round
(ROUND 2A). Round 1 (`results/ROUND1_VERDICT.md`, NEGATIVE UPDATE, commit
`206742f`) is not reopened, reinterpreted, or rerun by anything in this
document.**

## 1. Global CV-of-CVs is descriptive only

`docs/CV_OF_CV_INTERPRETATION.md` (Round 0) already established this:
`CV_CVs = SD(CV_i) / Mean(CV_i)`, computed once over the whole corpus
(1,613 candidate series), is a single dataset-level number. It cannot vary
across time or across studies, so it structurally cannot predict *which*
series, study, or period will decline more than another. This limitation
is not revisited or weakened here — it is the reason this round exists.

## 2. A prospective predictor requires multiple contemporaneous series within a shared context

To turn "CV-of-CVs" into something that could vary in time and therefore
carry prospective information, it must be redefined as a **group-level,
time-indexed** statistic:

```
C_g(t) = SD_i( CV_{i,t} ) / Mean_i( CV_{i,t} )
```

— computed across multiple series `i` that share a context `g` and are
jointly observed within a historical window ending at or before `t`. This
requires, structurally, that **more than one series exist within the same
context and the same historical period** — otherwise `SD_i(...)` is
undefined (a single value has no dispersion). Whether this requirement is
actually met by the real data, at any usable group size, is exactly what
Tasks 3–8 below audit.

## 3. Candidate context defaults to `DataSource_ID` (study)

The default context grouping `g` is **`DataSource_ID`** (study), for the
same reason it is the frozen grouping variable throughout Round 0/Round 1
(`docs/ANALYSIS_UNIT.md`): series within a study share methodology,
observers, and regional drivers, so they are the most defensible
"contemporaneous, comparable series" set. A more finely nested unit (e.g.
`DataSource_ID x Stratum`) is considered only if Task 3/9's audit shows
study-level grouping alone leaves too few series per group to compute
`SD_i(...)` meaningfully — **that determination is made from structural
counts alone (Task 3), never from outcome behavior.**

## 4. Predictor construction must use historical observations only

Every quantity computed in this round — series counts, year coverage,
contemporaneous overlap, window support, estimator stability — is derived
from `Year`, `Plot_ID`, `DataSource_ID`, `Stratum`, and non-outcome
abundance values (`Number`), treated purely as *counts and dates*, or, for
the estimator-stability audit (Task 6) only, as *historical-window CV
values themselves* (never a late-window or future-period value, and never
compared to any later value).

## 5. Future outcome must remain completely untouched this round

No function in `src/round2a_cv_of_cv_feasibility.py` reads, computes, or
references the `outcome` column, `ols_trend_slope` applied to a late
window, or any Round 1 modeling-table output. This is verified
mechanically, not just asserted in prose — see Task 12,
`results/ROUND2A_NO_PEEKING_AUDIT.md`.

## 6. Early-warning testing should distinguish LEVEL from CHANGE

Two structurally different candidate predictors are audited separately
(Task 8), because they have different data requirements:

- **LEVEL**: a single historical `C_g(t)` value, estimated once per
  context from one early historical window. Requires only one adequately
  supported historical meta-window per context.
- **CHANGE**: the slope/trend of `C_g(t)` across *multiple* historical
  meta-windows within the same context. Requires several
  (`>= 3`, per Task 8) adequately supported sequential historical windows
  per context — a strictly harder requirement than LEVEL.

Neither is assumed more likely to be informative than the other before
any outcome is examined — that judgment is deferred to a future,
separately-frozen H4.

## 7. Contextual value is not assumed universal

Not every study, stratum, or context is assumed to support a defensible
`C_g(t)` estimate. The audit tasks below report **counts and thresholds**,
not a single yes/no answer for the whole corpus — a future H4 would very
likely apply only to the subset of contexts meeting a frozen adequacy
gate (mirroring the Task 14 stratum gate already used in Round 0/Round 1),
not to the corpus as a whole.

## 8. Any eventual H4 must be frozen before predictor-outcome association is computed

This round's Task 13 output is a feasibility gate (READY / MARGINALLY
READY / UNDERPOWERED / BLOCKED) and, if warranted, a **single recommended
H4 design** — not an executed test. Freezing that design and then
computing any predictor-outcome association is explicitly deferred to a
future round, exactly mirroring the Round 0 -> Round 1 discipline already
used once in this project.

## No preferred result direction is specified here

Task 2's instruction is followed literally: no direction is asserted for
whether `C_g(t)`'s level or change should predict better or worse future
outcomes, beyond the one logical constraint the mechanism itself implies
(if meta-variability compression, rather than variability itself, is the
proposed signal, a *narrowing* of `C_g(t)` — not merely a low level —
would be the version of the original mechanism most analogous to the
already-tested, already-NEGATIVE, individual-series constraint
hypothesis). That analogy is noted only as context for why this idea was
proposed, not as a predetermined direction to be confirmed.
