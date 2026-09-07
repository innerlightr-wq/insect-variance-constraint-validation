# Hypothesis protocol — FROZEN before any predictor-outcome association is computed

**Freeze commit: this document is committed alongside the freeze commit
`freeze insect variance constraint validation protocol` and is not
modified afterward except by an explicitly logged, dated amendment that
does not touch already-executed results.** No H1/H2/H3 test, coefficient,
or p-value exists anywhere in this repository as of this freeze. All
counts cited below come from `results/DATA_ADEQUACY_AUDIT.md` and
`results/POWER_ADEQUACY_AUDIT.md`, both of which compute only structural
facts about the data and the outcome variable's own marginal distribution
— never any predictor-outcome association (no peeking).

**Central conceptual distinction, held throughout:** `constraint strength
!= target-specific predictive information`. A tight early-window variance
regime is scientifically interesting in this project only insofar as it
predicts the late-window outcome, out of sample, after conventional
predictors and study structure are controlled — not merely because it
describes the data.

---

## 1. Unit of analysis

See `docs/ANALYSIS_UNIT.md`. Frozen key: `(DataSource_ID, Plot_ID,
Stratum)`, `MetricAB == "abundance"` only for the primary analysis.

## 2. Primary outcome (Task 5)

For each eligible series (definition in §3):

1. Aggregate `Number` within each calendar year by summing across sampling
   periods (`insect_variance_protocol.aggregate_within_year`); a year with
   every period null is left null, never coerced to 0.
2. Split the series' usable (non-null-year) years chronologically into an
   EARLY window (first `ceil(n/2)` years) and a LATE window (remaining
   `floor(n/2)` years) — `insect_variance_protocol.chronological_split`.
   No year is ever in both windows; every late-window year is strictly
   later than every early-window year.
3. **Frozen primary outcome:** the ordinary-least-squares slope of
   `log1p(Number)` regressed on `Year`, computed using **only the LATE
   window's** years and values —
   `insect_variance_protocol.ols_trend_slope(late_years, log1p(late_values))`.
   A more negative slope means a steeper proportional decline (worse
   outcome); a positive slope means recovery/increase.
4. All candidate predictors (§4) are computed using **only the EARLY
   window's** years and values. No future observation is used in
   predictor construction — enforced structurally, since
   `chronological_split` asserts `max(early) < min(late)`.

`log1p`, not raw `Number` or plain `log`, is used for the outcome for two
reasons (full derivation: `docs/METRIC_PROPERTIES.md`): (a) `Number`
contains exact zeros (~4.0% of non-missing abundance rows), and plain
`log` is undefined at 0; (b) a slope on `log1p(Number)` approximates a
proportional (percent-per-year) trend, which is comparable across
differently-scaled studies, unlike a slope on raw counts.

**Abundance is the primary analysis; biomass is reserved for sensitivity
only** (Task 5) — the entire pipeline above is re-run, unchanged, on
`MetricAB == "biomass"` rows as a separate, clearly labeled sensitivity
analysis in a future round, never pooled with the abundance series.

## 3. Frozen eligibility rule (Task 6)

**Rule, chosen only after auditing the real empirical distribution of
series lengths (not chosen blindly and not later revised):**

- Minimum **10** usable (non-null-year) years per series.
- Chronological split as in §2 (`ceil(n/2)` / `floor(n/2)`), which
  guarantees **>= 5** points in each window whenever the 10-year minimum
  is met.
- No leakage across the split (structurally enforced, §2 point 4).

**Why 10, not some other number:** the real distribution of usable years
per candidate abundance series (`n = 1613` candidate series) has median
11, mean 13.2, and a visible floor at 2 (a small number of series have
almost all years aggregate to null). A cutoff of 10 retains **1,129 of
1,613 candidate series (70.0%)** across **99 distinct studies** — enough
for double-digit-fold grouped cross-validation with balanced fold sizes
(§7) — while still requiring a real, non-trivial early AND late window (5
points each is enough to fit a 1-parameter OLS trend with 3 residual
degrees of freedom). A lower cutoff (e.g. 6, which would retain 1,351
series) was considered and rejected because it would push the minimum
per-window size to 3, too thin for a trend slope to be anything but noise.
**This cutoff is frozen. It is not revisited if H1/H2 come back weak or
null.**

| | value |
|---|---:|
| candidate series (abundance, before eligibility) | 1,613 |
| eligible series (>= 10 usable years) | **1,129** |
| excluded | 484 (all for "fewer than 10 usable years") |
| eligible studies | **99** |
| median usable years (eligible) | 15 |
| median early-window points | 8 |
| median late-window points | 7 |
| range of usable years (eligible) | [10, 80] |

(Source: `results/POWER_ADEQUACY_AUDIT.md` / `.json`, computed with zero
reference to any predictor-outcome association.)

## 4. Frozen candidate predictors (Task 7)

**Conventional baseline features (all computed from the EARLY window
only):**

- `baseline_mean_log1p` — mean of `log1p(Number)` over early-window years
- `baseline_cv` — `insect_variance_protocol.coefficient_of_variation` of
  early-window `Number` (raw scale, per `docs/METRIC_PROPERTIES.md`'s
  monotonic-transform caution — CV and the constraint candidates below are
  all computed on the same raw scale as each other, distinct from the
  log1p scale used for the trend/outcome)
- `baseline_trend` — `ols_trend_slope` of `log1p(Number)` vs. `Year` over
  early-window years (same functional form as the outcome, applied to the
  early window — a genuinely prior, non-leaking feature)
- `baseline_n` — count of early-window usable years
- `baseline_span` — `max(early_years) - min(early_years)`

**Frozen constraint candidates (maximum 3, per Task 7), all computed on
early-window `Number`, raw scale — full derivations in
`docs/METRIC_PROPERTIES.md`:**

| id | metric | formula | frozen H1 direction |
|---|---|---|---|
| A | `D_{3/1}` | `M_3(x) / M_1(x)` | lower (closer to 1, tighter) -> more negative future trend (worse outcome) |
| B | `D_{4/1}` | `M_4(x) / M_1(x)` | lower (closer to 1, tighter) -> more negative future trend (worse outcome) |
| C | `Q_{90/50}` | `Quantile(x,0.90) / Quantile(x,0.50)` | lower (closer to 1, tighter) -> more negative future trend (worse outcome) |

All three share the same direction because all three share the same
"1 = maximally tight" minimum (§`docs/METRIC_PROPERTIES.md`, "ordering
property") — this is a mathematical consequence of the power-mean
inequality and the quantile-monotonicity argument, not an independently
chosen convention per metric.

**`CV_CVs` (the manuscript's global, dataset-level cross-study statistic)
is explicitly NOT used as an individual-series predictive feature** —
per Task 7's own instruction, it is a single dataset-level descriptive
number and has no defensible per-series, non-leaking definition. It is
treated entirely separately in `docs/CV_OF_CV_INTERPRETATION.md`.

## 5. Frozen hypotheses (Task 9)

### H1 — Out-of-sample constraint hypothesis

A frozen constraint metric (A, B, or C), measured in the early window,
predicts a worse (more negative) late-window trend, after controlling for
the conventional baseline features and study structure (grouped
cross-validation, §7). Direction frozen per-metric in §4's table, before
any test is run.

### H2 — Incremental information hypothesis

Adding the frozen constraint metric(s) to the conventional baseline model
improves **out-of-sample** prediction of the late-window outcome, compared
to baseline alone:

- **M0:** baseline features only (§4)
- **M1:** M0 + frozen constraint metric(s)

**Primary evidence is out-of-sample performance improvement, not a
coefficient p-value alone.**

- **PRIMARY performance metric: out-of-sample RMSE**, aggregated by
  pooling squared residuals across all grouped-CV test folds into one
  number (§7), then taking the square root — chosen as primary over R²
  because RMSE aggregates cleanly across folds of unequal size and unequal
  within-fold outcome variance (a real risk here — fold sizes and study
  composition vary, §7), whereas a fold-wise R² can become unstable or
  ill-defined in a low-variance fold. RMSE is also directly interpretable
  in the outcome's own units (log1p-abundance slope per year).
- **SECONDARY performance metric: out-of-sample R²** (`1 -
  SS_res/SS_tot`, computed the same pooled way), reported alongside RMSE
  for interpretability, never substituted for it if the two disagree.

### H3 — Ecological-stratum moderation (SECONDARY to H1/H2)

The H1/H2 relationship differs by ecological stratum. **Only tested for
strata passing the frozen adequacy gate** (Task 14, §6). **H3 is never
promoted to the main result if H1 and H2 both fail** — it is reported, if
at all, strictly as a secondary/exploratory follow-up.

## 6. Stratum adequacy gate (Task 14)

**Frozen thresholds:** a stratum is eligible for H3 moderation testing
only if it has **>= 30 eligible series AND >= 5 independent studies**.
Chosen, and confirmed still discriminating after inspecting the real
counts, before freezing:

| stratum | eligible series | eligible studies | adequate for H3 |
|---|---:|---:|---|
| Air | 406 | 40 | **Yes** |
| Water | 328 | 30 | **Yes** |
| Herb layer | 199 | 10 | **Yes** |
| Soil surface | 136 | 16 | **Yes** |
| Trees | 47 | 4 | **No** (studies < 5) |
| Underground | 13 | 4 | **No** (both < threshold) |

(Source: `results/POWER_ADEQUACY_AUDIT.md`.) **Trees and Underground are
excluded from H3 by this frozen gate — not revisited later.**

## 7. Frozen validation design (Task 10)

**Grouped, study-aware cross-validation is mandatory** — random row-wise
CV is prohibited, because series within the same study share methodology,
observers, and regional drivers (`docs/ANALYSIS_UNIT.md`).

- **Grouping field:** `DataSource_ID`.
- **Method:** `sklearn.model_selection.GroupKFold`, `n_splits = 10`
  (`insect_variance_protocol.make_group_folds`), applied to the 1,129
  eligible series across 99 studies.
- **Fold validity check (computed, not assumed):** minimum test-fold size
  across the 10 folds is **105** series (sizes: 151, 132, 106, 106, 106,
  106, 106, 106, 105, 105) — no fold is thin. Verified in
  `results/POWER_ADEQUACY_AUDIT.md`.
- **Fallback rule (frozen BEFORE any test, per Task 10):** if the minimum
  test-fold size falls below **20** series, reduce `n_splits` by 1 (floor
  of 5) and regenerate; if no value of `n_splits` in `[5, 10]` satisfies
  the floor, the design is `BLOCKED` for grouped CV as specified.
  **This fallback was not needed** — `n_splits = 10` already satisfies the
  floor with a wide margin (`fallback_triggered: false` in
  `results/power_adequacy_audit.json`).
- **Strata across folds:** not separately re-stratified — `GroupKFold`
  groups on study only. Whether every stratum appears in every fold is a
  descriptive fact to check at model-fit time in a later round, not a
  design requirement for H1/H2 (which pool across strata); it IS relevant
  for H3 and will be re-checked per-stratum before any H3 fold is trusted.
- **Number of folds is fixed at freeze time and is not tuned based on
  performance** — this document is the record of that commitment.

## 8. Frozen model (Task 11)

- **Primary model:** ordinary least-squares linear regression on
  standardized (z-scored) features.
- **Standardization is fit within each training fold only** (mean/SD
  computed on the training rows of that fold, applied to both train and
  test rows of that fold) — prevents any leakage of test-fold statistics
  into preprocessing.
- **No study fixed effects are encoded as model features** — a fixed
  effect keyed on `DataSource_ID` cannot generalize to a held-out study by
  construction (its dummy column would be entirely zero/undefined for an
  unseen study), which would silently leak study identity information
  into an "out-of-sample" claim. Study structure is handled exclusively
  through the grouped-fold design (§7), never through study-identity
  features.
- **No interaction terms, no polynomial expansion, no regularization
  tuning** in the primary model.
- **Predeclared fallback:** if OLS on the standardized design matrix shows
  a condition number so large that coefficient estimates are numerically
  unstable (checked mechanically via `numpy.linalg.cond` at model-fit
  time, threshold `> 1e8`, a standard numerical-stability convention, not
  an outcome-dependent choice), the frozen fallback is Ridge regression
  with a fixed, non-tuned `alpha = 1.0` on the same standardized features
  — chosen once, here, before any fold is fit, not selected after seeing
  which one performs better.
- **Model shopping is explicitly excluded this round:** no random forest,
  boosting, or neural network is fit as a primary model. A future,
  separately-frozen round may explore nonlinear models only as an
  explicitly labeled secondary/exploratory analysis.

## 9. Negative controls (Task 12)

Three controls, frozen before any test:

- **NC1 — within-study constraint permutation:**
  `insect_variance_protocol.permute_within_group(constraint_values,
  study_ids, seed)` — permutes each frozen constraint metric among
  eligible series *within the same study*, preserving each study's own
  marginal distribution of that metric and every series' true outcome and
  baseline features. **Expected behavior under a true null:** M1's
  out-of-sample performance advantage over M0 should collapse to
  approximately zero (within permutation-distribution noise).
- **NC2 — within-study outcome permutation:**
  `permute_within_group(outcome_values, study_ids, seed)` — permutes the
  late-window outcome among eligible series within the same study,
  preserving each series' true early-window predictors. **Expected
  behavior under a true null:** identical rationale to NC1, applied to the
  other side of the association.
- **NC3 — time-reversal / pseudo-future diagnostic:**
  `insect_variance_protocol.time_reversal_pseudo_future(early_values,
  late_values)` — swaps which window is treated as "predictor window" and
  which as "outcome window" for the *same* series (late-window summary
  statistics used to "predict" the early-window trend). **Explicitly
  defined expected behavior (per Task 12's own requirement that no
  ambiguous control be used):** this is a pipeline-artifact diagnostic,
  not a test of H1/H2 in either temporal direction. A positive result here
  (the reversed setup "predicting" well) would indicate a leaked
  time-invariant confound (e.g. a per-study constant driving both windows
  identically) and would trigger a pipeline audit, not be reported as
  evidence for or against H1/H2 in either direction.
- **Permutation count:** **2,000** permutations per control (matching this
  project's own established convention from a related project's frozen
  protocols — a fixed, moderate number chosen for computational tractability
  given three controls x three constraint metrics x grouped refitting,
  decided now, not adjusted after seeing how long it takes to run).

## 10. Multiple testing (Task 13)

**Frozen family for Holm correction:**

1. H1, metric A (`D_{3/1}`)
2. H1, metric B (`D_{4/1}`)
3. H1, metric C (`Q_{90/50}`)
4. H2, incremental performance (M1 vs. M0, primary metric = out-of-sample
   RMSE)

Holm's step-down procedure is applied across exactly these 4 tests, in
this fixed order, at `alpha = 0.05`. **H3, and any biomass sensitivity
analysis, are explicitly SECONDARY/EXPLORATORY and are not included in
this primary Holm family** — they are reported, if run, with their own
p-values clearly labeled as not multiplicity-corrected against the
primary family, per Task 13's explicit separation of PRIMARY / SECONDARY /
EXPLORATORY.

## 11. What would count as support, and what would count as failure

- **H1 support (per metric):** Holm-adjusted p < 0.05 for the frozen
  direction in §4, from a properly grouped, out-of-sample procedure.
- **H1 failure (per metric):** Holm-adjusted p >= 0.05, OR a
  statistically real effect in the *opposite* direction from the frozen
  prediction.
- **H2 support:** M1's pooled out-of-sample RMSE is lower than M0's by an
  amount that survives the frozen permutation-based significance
  assessment (NC1/NC2 provide the null-comparison distributions) after
  Holm correction.
- **H2 failure:** no significant RMSE improvement, or R² (secondary)
  contradicts RMSE's direction in a way that indicates the primary metric
  result is not robust.
- **Clean negative result condition (the specific thing this protocol is
  designed to be capable of returning):** all of H1(A), H1(B), H1(C), and
  H2 fail to reach Holm-adjusted significance. This is a valid, reportable
  outcome under this frozen protocol, exactly as it was for every prior
  round of the `linear-a-constraint-validation` project's own discipline
  that this project explicitly follows.
