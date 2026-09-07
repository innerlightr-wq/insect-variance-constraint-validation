# H4 protocol — historical CV-of-CVs as a prospective early-warning indicator

**FROZEN BEFORE EXECUTION.** Parent feasibility commit: `d3246d9`
(Round 2A, verdict `MARGINALLY READY` for a LEVEL-only H4). Round 0
(`21e6992`) and Round 1 (`206742f`, verdict `NEGATIVE UPDATE`) are
unmodified and not reopened. **No predictor-outcome association has been
computed anywhere in this freeze round** — see
`results/H4_FREEZE_NO_PEEKING_AUDIT.md`.

H4 is **not** a rerun of Round 1. Round 1 tested three *individual-series*
early-window constraint metrics (`D3/1`, `D4/1`, `Q90/50`) — all
`NOT SUPPORTED`. H4 tests a structurally different, *study-level,
hierarchical* quantity: the historical dispersion **of** per-series CVs
across multiple contemporaneous series sharing a study context.

---

## 1. Primary scientific question (Task 2)

> Does historical study-level CV-of-CVs contain prospective information
> about subsequent insect abundance deterioration?

Temporal ordering, enforced structurally (§8, §14 of this document):

```
HISTORICAL META-VARIABILITY  (C_g, built only from a study's shared
                               first-10-usable-year window)
        |
        v
FUTURE ABUNDANCE CHANGE      (each contributing series' own outcome,
                               required to fall entirely after that
                               same cutoff)
```

**H4 is a LEVEL hypothesis only.** CHANGE (the slope/trend of `C_g` across
multiple historical windows) is **excluded**, because Round 2A Task 8
found it underpowered at every tested multiplicity (14/99 studies at
`>=3` sequential adequate windows, 4 at `>=4`, 3 at `>=5`). **No secondary
CHANGE test may be run after H4, in this round or any future one, unless
a wholly new, independently-frozen feasibility audit establishes adequate
support for it.**

---

## 2. Context and inferential unit (Task 3)

- **Context grouping: `DataSource_ID`** (study) — the Round 2A default,
  confirmed, not a finer stratum-nested context (Round 2A's own audit
  explicitly declined to assume finer-grouping adequacy without a
  separate support audit, `docs/CV_OF_CV_INFERENCE_UNIT_AUDIT.md` §"multiple
  strata").
- **Inferential unit for `C_g` itself: the (study, historical-window)
  pair** — Round 2A froze exactly **one** non-overlapping historical
  window per study (`results/ROUND2A_FEASIBILITY_GATE.md`: "Minimum valid
  historical windows required: **1**"; "Overlapping windows: **Not
  used**"). This is frozen as-is, verbatim — not the larger-N,
  multiple-study-window alternative.
- **Number of constituent series vs. effective inferential N — kept
  explicitly distinct throughout:**
  - **Constituent series** ("`i`" in `C_g = SD_i(CV_i)/Mean_i(CV_i)`): all
    Round-1-eligible series with `>=2` usable observations within a
    study's frozen historical window. This count can be large (a study
    meeting the adequacy gate has `>=15` such series, by construction).
  - **Effective inferential N for any claim about `C_g`'s own explanatory
    power**: the number of **adequate study-windows** — expected
    approximately 19-20 (Round 2A's own estimate at the `>=15`-series bar,
    §4). **Never** the number of series or plots broadcast onto those
    studies (~hundreds to low thousands). Any H4 result reported with
    "n = [series count]" as its sample size for `C_g`'s effect is
    invalid under this protocol.

---

## 3. Adequacy threshold (Task 4)

**Frozen: minimum constituent series per meta-variability estimate,
`n >= 15`.** Motivated entirely by Round 2A's estimator-stability audit
(`docs/CV_OF_CV_ESTIMATOR_PROPERTIES.md`, `results/CV_OF_CV_ESTIMATOR_STABILITY.md`),
run and fixed **before** any outcome was inspected. **`n>=5`, `n>=10`,
`n>=20`, `n>=30` were audited only as part of the already-completed
feasibility exploration and MUST NOT be used as alternate H4
specifications, before or after seeing H4's result.**

---

## 4. Historical window (Task 5)

**Frozen: 10 years**, matching Round 1's own `MIN_TOTAL_POINTS` convention
and Round 2A's own Design-C implementation. Exact definition, copied
verbatim from `src/round2a_cv_of_cv_feasibility.py`'s `chronology_design_feasibility`
(design `C_fixed_10yr_history_plus_heldout_later`), not reinterpreted:

- **Observation-count / rank-based, not calendar-year arithmetic.** A
  study's historical window is the first **10 elements of the sorted,
  deduplicated union of usable years across all of that study's
  Round-1-eligible series** — `all_years[:10]` where `all_years =
  sorted(set(union of each eligible series' own usable years))`. This is
  **not** "calendar year `Y0` through `Y0+9`" — a study with sparse early
  coverage (gap years contributed by no series at all) has its 10-year
  window stretch across more than 10 calendar years, exactly mirroring
  `insect_variance_protocol.chronological_split`'s own rank-based logic
  used throughout Round 0/Round 1.
- **Minimum observations per constituent series within the window:**
  `>=2` usable years within `hist_years` — the same floor
  `coefficient_of_variation` itself already requires (Round 0,
  `docs/METRIC_PROPERTIES.md`), unchanged.
- **Missing years:** a constituent series contributes only its own
  actually-observed (non-null-after-aggregation) years within the window;
  a gap year contributes nothing for that series (unchanged
  `aggregate_within_year` convention — see §5).
- **Unequal sampling across constituent series:** not equalized or
  weighted — each series' CV is computed from however many usable years
  it happens to have within the window (`>=2`), exactly as Round 2A's own
  Task 5/6 characterized (a disclosed, not hidden, source of unequal
  per-series precision, `docs/CV_OF_CV_METRIC_AUDIT.md` item 7).
- **Rolling or non-overlapping:** **non-overlapping** — exactly **one**
  window is ever constructed per study (the first 10 union-years), never
  a rolling scan for a "better" window.
- **How the qualifying window is selected:** **deterministic, with no
  outcome dependence** — always the study's own first 10 union-years, full
  stop. A study is **excluded** if it has fewer than 11 total union-years
  (needs the window itself plus at least 1 future year) or fewer than 15
  constituent series with `>=2` observations inside that fixed window.
  There is no search over alternative windows within a study; the frozen
  design admits exactly one candidate per study, by construction.

---

## 5. Per-series CV calculation (Task 6)

**Unchanged from Round 0/Round 1, reused verbatim — no new rule
introduced:**

```
CV_i = SD_i / Mean_i     (insect_variance_protocol.coefficient_of_variation)
```

- **Scale:** raw `Number` (abundance), never `log1p`-transformed —
  matches CV's proven multiplicative scale invariance
  (`docs/METRIC_PROPERTIES.md`).
- **SD convention:** **sample** SD (`ddof=1`), matching the existing
  frozen implementation exactly.
- **Zero mean:** `CV_i` is `None` (undefined), not coerced to 0 or `inf` —
  a series with `None` cannot be a constituent series for that window
  (excluded from `C_g`'s constituent set, not from the study's other
  candidacy).
- **Near-zero mean:** no special threshold beyond exact-zero is
  introduced; Round 2A's own audit found no near-zero-denominator cases
  in the real historical CV pool at any tested group size
  (`results/CV_OF_CV_ESTIMATOR_STABILITY.md`, frequency 0.000 throughout)
  — not revisited here.
- **Missing observations / minimum observations:** `>=2` usable years
  required (§4); fewer than 2 makes `coefficient_of_variation` return
  `None` by the function's own existing contract.
- **Duplicated observations (multiple sampling periods within one
  calendar year):** unchanged — `aggregate_within_year` sums `Number`
  across periods within a (study, plot, stratum, year) cell before any CV
  is computed (Round 0's frozen, disclosed rule, `docs/HYPOTHESIS_PROTOCOL.md`
  §2).
- **Extreme values:** **no winsorization, trimming, or robustification is
  introduced.** `docs/CV_OF_CV_METRIC_AUDIT.md` item 8 named these only as
  candidates for *future* consideration, explicitly not adopted this
  round. **No post-result outlier removal is permitted at any point,
  before or after H4 is executed (§13).**

---

## 6. Meta-variability predictor `C_g` (Task 7)

```
C_g = SD_i(CV_i) / Mean_i(CV_i)
```

computed once per study over its `>=15` qualifying constituent series'
CVs, all drawn from the same frozen 10-year historical window (§4),
implemented as `round2a_cv_of_cv_feasibility.cv_of_cvs` (unchanged,
reused verbatim from Round 2A).

**`C_g` is contextual, not universal.** H4 does **not** test, and no
result under this protocol may be interpreted as testing:

- whether `C_g` (or the global `CV_CVs`) is a universal constant across
  studies;
- whether any specific numerical value — **`0.610`** (the original
  manuscript's reported global figure) or **`0.512`** (this project's own
  independently-recomputed global figure, `docs/CV_OF_CV_INTERPRETATION.md`)
  — is universal or ecologically special in any way.

**The only question H4 asks:** does *variation* in historical `C_g`
*across* the ~19-20 eligible study-contexts carry prospective information
about each context's own subsequent ecological change, beyond the
conventional baseline (§9)?

---

## 7. Chronology (Task 8) — Design C, copied verbatim

Per §4, Design C is: **fixed 10-year history window (the study's own
first 10 union-years), then a fully held-out later period** (all
remaining union-years for that study). No fractional split (Design A
50/50, Design B 60/40) is used — Round 2A's own recommendation table
selected Design C specifically for its clean, non-arbitrary future
boundary and superior median future-year availability
(`results/ROUND2A_FEASIBILITY_GATE.md`).

- **Historical predictor period:** the study's first 10 union-years
  (`hist_years`), exactly as defined in §4.
- **Separation point:** the 10th union-year itself; every subsequent
  union-year belongs to the future period.
- **Future outcome period:** all of a study's remaining union-years after
  `hist_years` (`fut_years`) — not restricted to a fixed length.
- **Minimum future observations:** governed entirely by Round 1's own
  already-frozen outcome-validity requirement, reused unchanged (§8-9
  below) — a *given constituent-eligible series'* Round-1 late window must
  itself satisfy Round 1's own `>=5`-usable-years-per-window rule; H4
  introduces no separate, new minimum beyond that.
- **Handling of unequal series lengths:** unchanged — `hist_years` is
  defined at the study level (union across series), so series of
  different lengths simply contribute whatever overlap they individually
  have with the fixed window (§4/§5).
- **Treatment of calendar gaps:** unchanged, rank-based (§4) — a
  calendar-year gap with zero eligible-series coverage does not "use up"
  a slot in the 10-year window.
- **Leakage protections:** identical assertion-based guarantee already
  used throughout Round 0/Round 1
  (`insect_variance_protocol.chronological_split`'s pattern): `hist_years`
  and `fut_years` partition the study's union-years with
  `max(hist_years) < min(fut_years)` by construction of a rank-based,
  non-overlapping split. **No future observation is used to compute
  `C_g`** — enforced both by this construction and by the machine-checked
  no-peeking guard (`src/h4_no_peeking_guard.py`, Task 20).

---

## 8-9. Future outcome (Task 9) — resolving Round 2A's own open question

Round 2A's Task 9 audit explicitly identified, but did **not** resolve,
which of three candidate ways to pair `C_g` (a study-level quantity) with
Round 1's per-series outcome definition (`results/ROUND2A_FEASIBILITY_GATE.md`:
"one ... outcome measure (collapsed or per-series, to be decided at
freeze time — see Task 9's own unresolved options 1-3)"). Per this
freeze round's own Task 9 instruction, that gap is resolved here **only**
if a unique choice follows from already-frozen material — not invented.
**It does follow, from two already-frozen constraints taken together, not
from a new preference:**

1. Round 2A's own recommended inference scheme explicitly "mirrors Round
   1's NC1/NC2" (`results/ROUND2A_FEASIBILITY_GATE.md`, "Study
   grouping/clustering for inference" row). Round 1's NC1/NC2 permute
   values **within study across multiple series** — an operation that is
   only meaningful if the H4 analysis table has **more than one row per
   study** (i.e., series-level rows), not one collapsed row per study.
   This alone rules out collapsing outcomes to one value per study
   (Round 2A's candidate options 1 and 2), because collapsing would leave
   nothing to permute within a study.
2. Collapsing series outcomes into one per-study number (options 1/2)
   would additionally require **inventing a new cross-series aggregation
   rule** (mean? median? variance-weighted?) that neither Round 0 nor
   Round 1 ever froze — exactly the kind of silent invention this
   protocol must not introduce.

**Resolution: H4 reuses Round 1's own per-series outcome value verbatim,
unchanged, for every constituent series that individually qualifies**
(candidate option 3), **with exactly one new, temporally-forced
eligibility filter, not a new outcome formula:**

> A Round-1-eligible series may contribute an outcome row to H4 **only
> if that series' own Round-1 late window (its `late_year_min`) falls
> strictly after the study's H4 historical cutoff** — i.e.
> `series.late_year_min > max(study.hist_years)`.

This filter is not a free design choice — it is the unique condition
required to keep the "historical meta-variability -> future abundance
change" arrow (§1) true for every row, given that Round 1's own per-series
early/late split (`ceil(n/2)`/`floor(n/2)` of *that series'* own usable
years) does not automatically align with the *study-level* 10-year cutoff
`C_g` is built from. Without this filter, a short series entirely
contained within the study's historical window could have its Round-1
"outcome" computed from years that are not actually later than `C_g`'s
own historical boundary — a genuine leakage risk this filter eliminates
structurally, verified per-row (§14, no-peeking guard).

**Exact outcome formula reused, unchanged, from Round 1
(`docs/HYPOTHESIS_PROTOCOL.md` §2, `insect_variance_protocol.ols_trend_slope`):**
the OLS slope of `log1p(Number)` on `Year`, computed over that series' own
Round-1 late window. **No new outcome formula is introduced. No
biomass, bioacoustic, paleontological, or species-richness outcome is
used, considered, or substituted.**

**Baseline features (§9 below) are likewise Round 1's own per-series
values, unchanged** — they are not re-windowed to the study-level cutoff.
This is a disclosed simplification, not an oversight: Round 1's baseline
features are, by Round 1's own construction, already guaranteed to
precede that same series' own outcome window (Round 1's leakage
guarantee, unchanged); they characterize a per-series nuisance control,
not the study-level historical-meta-variability quantity under test, so
realigning them to `C_g`'s own cutoff is not required by the temporal
claim H4 actually makes.

---

## 10. Predeclared direction (Task 10)

**One-sided.** Derived only from the original manuscript's motivating
conceptual analogy (`docs/CV_OF_CV_EARLY_WARNING_CONCEPT.md` item 8) —
**not from inspecting any real outcome value in this or any prior round.**

The original manuscript's "bounded distribution" framing treated a
*tight* population-level CV-of-CVs as evidence of a shared ecological
constraint — directly analogous to the individual-series logic Round 1
already froze and tested ("tighter constraint -> worse future outcome",
`docs/HYPOTHESIS_PROTOCOL.md` §4-5, where a *lower* metric value, closer
to each metric's own minimum, was the "tight/constrained" end). Applying
the identical analogy one level up:

> **Predicted direction: a LOWER historical `C_g` (tighter, more
> homogeneous meta-variability across a study's contemporaneous series)
> predicts a WORSE (more negative) future abundance trend. Equivalently,
> the predicted sign of `C_g`'s coefficient in a model of the future
> outcome is POSITIVE** — exactly the same sign convention Round 1 froze
> for `D3/1`, `D4/1`, and `Q90/50` (`H1_DIRECTION = +1` for all three,
> `src/round1_execute.py`).

This is not directionally ambiguous under the motivating theory as
originally stated, so H4 is frozen **one-sided**, not two-sided.

---

## 11. Baseline / conditional test (Task 11)

**M0 (baseline):** Round 1's own frozen conventional baseline columns,
unchanged, reused verbatim per constituent-eligible series —
`baseline_mean_log1p, baseline_cv, baseline_trend, baseline_n,
baseline_span` (`round1_pipeline.BASELINE_COLS`). No new covariate is
added "because it seems useful now" — only what Round 1 already
established and Round 2A's own design table endorses ("against the same
conventional baseline used in Round 1").

**M1 (augmented):** M0 **+ `C_g`** (the study's single historical
meta-variability value, broadcast identically to every one of that
study's outcome-contributing series, per §8-9).

**Primary scientific question, restated exactly:** does `C_g` provide
target-specific prospective information beyond the frozen conventional
baseline — not whether `C_g` correlates with the outcome on its own,
unconditionally.

---

## 12. Inference (Task 12)

**Exact algorithm, frozen:**

1. **Model:** ordinary least squares, standardized features (mean/SD
   computed on the relevant training fold only — same convention as
   Round 1, `src/round1_execute.py`'s `_fit_predict_fold`), identical
   Ridge fallback (`alpha=1.0`, triggered only if the training design
   matrix's condition number exceeds `1e8`) — unchanged from Round 1's
   own frozen model spec, reused rather than reinvented.
2. **Cross-validation for the primary statistic:** **leave-one-study-out
   (LOSO)** — `n_splits = number of H4-eligible studies` (expected
   ~19-20). This is the forced, non-arbitrary generalization of Round 1's
   `GroupKFold(DataSource_ID)` to a much smaller cluster count: Round 1
   picked a fixed `n_splits=10` because it had 99 studies to spread across
   folds; H4's effective N (§2) is too small for a fixed, smaller-than-N
   fold count to be anything but an arbitrary new choice, so the unique,
   parameter-free choice is `n_splits = n_studies` (ordinary
   leave-one-group-out).
3. **Coefficient/statistic of interest (secondary, §13):** the
   standardized coefficient on `C_g` in a full-sample OLS of the outcome
   on M1's features.
4. **Clustering unit:** `DataSource_ID`, for both the LOSO folds
   themselves and (where reported) cluster-robust standard errors on the
   secondary coefficient — but see point 6.
5. **Permutation scheme (primary inference mechanism, not merely a
   robustness check — per this round's own Task 12 instruction that
   permutation be treated as primary given the small effective N):**
   **between-study permutation of `C_g`.** Round 2A's own instruction to
   "mirror Round 1's NC1/NC2" cannot be applied literally
   (`C_g` does not vary *within* a study — there is nothing to permute
   within one study's own rows, unlike Round 1's series-level metrics).
   The unique valid adaptation: **randomly permute which H4-eligible study
   is assigned which OTHER eligible study's own historical `C_g` value**
   (a permutation of the study-to-`C_g` mapping across the ~19-20
   eligible studies), while every series' own outcome, baseline features,
   and study membership (for LOSO clustering) are held fixed. This
   severs the `C_g`-to-outcome link while preserving every other piece of
   the design's dependence structure — the direct study-level analogue of
   Round 1's within-study permutation, forced by `C_g`'s own coarser
   (study-level, not series-level) granularity.
6. **Exchangeability restriction:** studies are permuted only among the
   H4-eligible set (~19-20 studies) — never against studies that failed
   the adequacy gate (§3-4), and never mixed with Round 1's own
   series-level NC1/NC2 machinery, which operates on a different
   granularity and a different, already-closed hypothesis family.
7. **Permutation count: 10,000.** Round 2A did not itself freeze a
   permutation count for H4 (its own 1,000-resample bootstrap, Task 6,
   was a separate, already-completed estimator-stability exercise, not an
   inference procedure) — so this round's own default of 10,000 applies,
   per this prompt's explicit instruction. With ~19-20 eligible studies,
   `19!`/`20!` possible relabelings vastly exceeds 10,000, so this is a
   random (not exhaustive) sample of the permutation distribution.
8. **Seed: `20260907`** — this project's own established convention,
   unchanged.
9. **One-sided vs. two-sided:** **one-sided**, matching §10's predeclared
   direction — the permutation p-value is the fraction of null-distribution
   `ΔRMSE` values `>=` the observed `ΔRMSE`, with the standard `(+1)/(+1)`
   continuity correction, identical formula to Round 1's NC1/NC2
   (`(count + 1) / (n_permutations + 1)`).
10. **Significance threshold: `alpha = 0.05`** — unchanged project
    convention.
11. **Ties:** included in the `>=` comparison exactly as Round 1's own
    NC1/NC2 implementation already does (no separate tie-breaking rule
    needed beyond the inclusive `>=`).
12. **Formula for the permutation p-value:**
    `p = (1 + #{b : ΔRMSE_perm[b] >= ΔRMSE_observed}) / (10000 + 1)`.

---

## 13. Primary statistic (Task 13)

**Exactly one primary H4 statistic, per this round's own instruction —
Round 2A's "both an H1-style and an H2-style check" recommendation is
honored by demoting the H1-style check to explicitly secondary, not by
running two co-primary tests:**

> **PRIMARY: incremental out-of-sample predictive performance,
> `ΔRMSE = RMSE(M0) - RMSE(M1)`, pooled across leave-one-study-out folds
> (§12.2), sign convention identical to Round 1 (`positive ΔRMSE =
> improvement from adding `C_g`).** H4's support decision (§14) is gated
> on this statistic and its permutation p-value (§12.5-12.12) — not on
> the secondary coefficient alone, directly continuing this project's own
> established standard from Round 1 ("a significant individual
> coefficient alone is insufficient").

> **SECONDARY (cannot rescue a failed primary result, §14): the
> standardized OLS coefficient on `C_g}` in the full-sample M1 fit
> (§12.3), its predicted sign (positive, §10), and its permutation
> p-value under the identical between-study permutation scheme (§12.5).**

---

## 14. Support criterion (Task 14)

- **SUPPORTED:** `ΔRMSE > 0` (M1 genuinely outperforms M0 out-of-sample,
  §13 primary) **AND** the primary permutation p-value `<= 0.05`
  (one-sided, §12.9-12.12). Coefficient significance alone, without both
  conditions on the primary statistic, is **never** sufficient.
- **NOT SUPPORTED:** the primary permutation p-value `> 0.05`, regardless
  of `ΔRMSE`'s sign, OR `ΔRMSE <= 0` regardless of the p-value.
- **DIRECTIONALLY OPPOSITE:** the primary permutation test would reject
  the null at `alpha=0.05` **against** the predicted direction — i.e.
  `ΔRMSE` is reliably **negative** (M1 reliably *worse* than M0) by the
  same one-sided permutation logic applied to the opposite tail. (Given
  §10's one-sided freeze, this is assessed as a distinct, explicitly
  labeled outcome, not folded into "NOT SUPPORTED" silently.)
- **UNINTERPRETABLE / BLOCKED:** fewer than the frozen minimum number of
  H4-eligible studies survive to permit LOSO-CV at all (operationally: if
  fewer than 10 studies pass every gate in §3-4/§8-9, LOSO with that few
  folds is not a meaningful cross-validated estimate and the result is
  reported as UNINTERPRETABLE / BLOCKED, not forced into a SUPPORTED/NOT
  SUPPORTED box) — a structural, pre-specified floor, not a post-hoc
  excuse.
- **The secondary coefficient/p-value (§13) is reported alongside, always
  labeled secondary, and can never upgrade a NOT SUPPORTED or
  DIRECTIONALLY OPPOSITE primary result to SUPPORTED.**

---

## 15. STOP rule (Task 15)

**After H4 is executed, none of the following may occur, regardless of
result:**

- no alternate constituent-series thresholds (`n>=5/10/20/30`);
- no alternate historical windows (3/5/7-year, or any window other than
  the frozen first-10-union-years);
- no alternate chronological split (Design A/B, or any variant of Design
  C);
- no robust/winsorized/trimmed CV variant;
- no alternate transformation (e.g. `log1p` for `C_g` or CV);
- no removal of "inconvenient" studies beyond the frozen adequacy gate;
- no alternate future outcome (no biomass, bioacoustic, paleontological,
  or richness substitute; no re-windowed outcome beyond §8-9's single
  frozen filter);
- no alternate aggregation of constituent series into `C_g`;
- no subgroup search (by stratum, realm, or any other covariate) to
  rescue a failed H4;
- no CHANGE hypothesis, in this round or triggered by a failed H4;
- no increase in permutation count beyond 10,000;
- no alternative model family (no random forest, boosting, or other
  nonlinear model substituted for the frozen OLS/Ridge-fallback spec).

**If H4 fails (`NOT SUPPORTED` or `DIRECTIONALLY OPPOSITE`), the primary
conclusion is exactly:** historical LEVEL CV-of-CVs, as prospectively
defined by this protocol, is not supported as an early-warning indicator
in these data. No weaker or requalified restatement of this conclusion
is permitted without a wholly new, independently-frozen protocol.
