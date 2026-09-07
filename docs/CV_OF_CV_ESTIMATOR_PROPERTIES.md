# CV-of-CVs estimator properties (ROUND 2A, Task 6)

**Not a hypothesis test.** This document records the frozen bootstrap
design used to characterize `CV_of_CVs = SD(CV_i)/Mean(CV_i)`'s own
numerical behavior at realistic group sizes, using only the real,
historical (full-usable-span) per-series CV pool (n=1,129, the same
population `docs/CV_OF_CV_INTERPRETATION.md`/Round 0 already computed) —
never any future/outcome value.

## Frozen design (fixed before Task 6 was executed)

- **Resample count: 1,000** per group size — a round, computationally
  cheap number chosen for tractability across 6 group sizes; not tuned
  after inspecting how estimates behaved.
- **Seed: `20260907`** — this project's own established convention
  (matches the seed already used for Round 1's grouped CV).
- **Sampling scheme:** simple random sampling *without replacement* from
  the real 1,129-value historical CV pool, for each of the group sizes
  `n = 3, 5, 10, 15, 20, 30`.
- **Sensitivity diagnostic:** for each resample, one element is replaced
  with the pool's own maximum CV value, and the resulting shift in
  `CV_of_CVs` is recorded — a direct, disclosed operationalization of
  "sensitivity to one extreme CV."

## Findings (results/CV_OF_CV_ESTIMATOR_STABILITY.md, results/cv_of_cv_estimator_stability.json)

- **Never undefined, never near-zero-denominator**, at any tested group
  size (0.000 frequency across all six) — the historical CV pool has no
  series with a near-zero mean CV across resamples of this size, so the
  `SD/Mean` ratio is numerically safe in this specific pool.
- **Bootstrap CI width shrinks monotonically with `n`**: 0.779 at n=3,
  0.673 at n=5, 0.521 at n=15, 0.486 at n=30 — the estimator does
  stabilize as group size grows, as expected, but remains fairly wide
  even at n=30 relative to the pool's own mean CV_of_CVs-equivalent scale
  (mean estimate rises from 0.366 at n=3 toward ~0.47 at n=30, still
  below the Round 0 full-sample value of 0.512 — a known small-sample
  downward bias of this ratio estimator, not a new finding, but disclosed
  here since it directly bears on Task 13's minimum-group-size
  recommendation).
- **Single-extreme-value sensitivity decreases with `n`** (0.680 at n=3
  down to 0.329 at n=30) but is **never small** — even at n=30, swapping
  one of 30 constituent series' CV for the pool maximum shifts the
  group's `CV_of_CVs` by an average of 0.33, roughly two-thirds of the
  estimate's own typical magnitude. **This is the single strongest
  numerical caution this audit produces**: `CV_of_CVs` at any group size
  tested remains materially driven by its single most extreme
  constituent series, not merely refined by adding more series.

## Implication for a minimum defensible group size (feasibility only, not a threshold selection)

No single "correct" minimum is asserted here. What is established: `n=3`
and `n=5` show both wide CIs (>0.65) and the largest one-value
sensitivity — a group this small is not numerically defensible as a
stable estimate of anything. `n>=15-20` is where CI width first drops
below 0.6 and sensitivity below 0.5. This observation is available to
Task 13's feasibility-gate recommendation; it is not, itself, a decision.
