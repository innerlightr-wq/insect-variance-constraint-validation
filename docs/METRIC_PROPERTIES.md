# Metric properties — mathematical audit (Task 8)

**This is a mathematical audit, not a hypothesis test.** No association
between any metric below and the future outcome is computed anywhere in
this document. All derivations are exact (finite arithmetic / algebra),
verified computationally in `tests/test_insect_variance_protocol.py`
against synthetic constructions with known answers.

## Definitions

For a finite set of non-negative values `x = (x_1, ..., x_n)`:

```
M_p(x) = ( mean(x_i^p) )^(1/p),   p != 0
```

the **power mean** of order `p`. `M_1` is the ordinary arithmetic mean.

Frozen constraint-metric family (Task 7):

- **Candidate A:** `D_{3/1}(x) = M_3(x) / M_1(x)`
- **Candidate B:** `D_{4/1}(x) = M_4(x) / M_1(x)`
- **Candidate C:** `Q_{90/50}(x) = Quantile(x, 0.90) / Quantile(x, 0.50)`

Baseline (conventional): `CV(x) = SD(x) / M_1(x)`.

## Scale invariance (multiplicative)

**Claim:** all four statistics above are invariant under `x -> c*x` for any
constant `c > 0`.

**Proof for `D_{p/1}` (covers Candidates A and B, and generalizes to any
power-mean ratio):**

```
M_p(c*x) = ( mean((c*x_i)^p) )^(1/p) = ( c^p * mean(x_i^p) )^(1/p) = c * M_p(x)
```

for any `p != 0` and `c > 0` (the `p`-th root of `c^p` is `c` exactly when
`c > 0`, avoiding any branch/sign ambiguity). Therefore:

```
D_{p/1}(c*x) = M_p(c*x) / M_1(c*x) = (c*M_p(x)) / (c*M_1(x)) = D_{p/1}(x)
```

**exactly**, for every `c > 0` — the `c` cancels. This holds for `p = 3`
(Candidate A) and `p = 4` (Candidate B) identically; the proof does not
depend on the specific power chosen. `test_power_mean_ratio_scale_invariance`
verifies this numerically across a grid of `c` values and random positive
vectors.

**Proof for `Q_{90/50}`:** quantiles are equivariant under positive
scaling — `Quantile(c*x, q) = c * Quantile(x, q)` for `c > 0`, because
scaling by a positive constant preserves the order of all elements
exactly. Hence `Q_{90/50}(c*x) = (c*Q90(x)) / (c*Q50(x)) = Q_{90/50}(x)`.
`test_quantile_ratio_scale_invariance` verifies this numerically.

**`CV` is invariant by the identical argument** (`SD(c*x) = c*SD(x)`,
`M_1(c*x) = c*M_1(x)`), included here only as the familiar baseline case
this project's frozen candidates are designed to match in invariance
class, not as a new claim.

**Consequence:** because abundance is recorded on incommensurable raw
scales across the ~99-166 different original studies in this corpus (a
sweep-net count is not a pitfall-trap count is not a light-trap catch),
using a scale-**variant** statistic (e.g. raw variance, raw range) as a
cross-study predictor would conflate genuine ecological signal with pure
sampling-effort/unit differences. All three frozen constraint candidates,
by construction, cannot be driven by this artifact — a study that
happens to report numbers ten times larger due to trap density or unit
choice produces the *identical* `D_{3/1}`, `D_{4/1}`, and `Q_{90/50}`
value.

## Ordering property (why "1" is the tight/constrained end)

By the power-mean inequality, for non-negative `x` and `p > 1`:
`M_p(x) >= M_1(x)`, with **equality if and only if `x` is constant**
(zero within-series dispersion). Therefore:

```
D_{3/1}(x) >= 1,   D_{4/1}(x) >= 1,   for all non-negative x
```

with the minimum value `1` attained exactly at zero dispersion — the
"tightest" possible constraint. `Q_{90/50}(x) >= 1` for non-negative,
non-decreasing quantiles by the same constant-series argument (Q90 = Q50
iff the upper 10% of the distribution does not exceed the median, which
for a non-degenerate distribution with `Q90 != Q50` requires `Q90 > Q50`
whenever there is any dispersion above the median). This ordering is the
basis for each metric's frozen H1 direction in `docs/HYPOTHESIS_PROTOCOL.md`
— "tighter constraint" is operationalized as "closer to this metric's own
minimum of 1," never as an arbitrary sign choice.

## Sensitivity audit

| property | finding |
|---|---|
| **sensitivity to zeros** | `M_p` for `p > 0` is well-defined and finite when some `x_i = 0` (a zero contributes `0^p = 0` to the mean) — no special-casing needed for Candidates A/B. `Q_{90/50}` is well-defined unless the *median itself* is 0 (see "undefined cases"). |
| **sensitivity to extreme counts** | Candidates A and B (higher powers) are **increasingly sensitive** to the single largest observation as `p` grows — this is the intended, disclosed behavior (they are explicitly higher-*order* dispersion statistics, more sensitive to tail mass than `CV`). `Q_{90/50}` is comparatively **robust**: it depends only on rank/order statistics, not on the magnitude of the single largest value beyond the 90th-percentile boundary. This contrast is deliberate — the three candidates are not redundant, they trade off sensitivity vs. robustness to the single most extreme early-window observation. |
| **minimum sample size** | `M_p` requires `n >= 1` (defined even for a single point, trivially `D=1`, uninformative). `CV` requires `n >= 2` (needs a variance estimate). `Q_{90/50}` requires enough points for the 90th percentile to be a meaningful order statistic — with the frozen minimum of 5 early-window points, the 90th percentile is an interpolated value between the 4th and 5th of 5 sorted points (NumPy's default linear interpolation), not a single raw observation; this is disclosed as a real, if modest, small-sample interpolation dependency, not hidden. |
| **undefined cases** | `D_{p/1}` is undefined (0/0) iff `M_1(x) = 0`, i.e. **every value in the window is exactly 0**. `Q_{90/50}` is undefined iff `Quantile(x,0.5) = 0`. Frozen handling: `power_mean_ratio` and `quantile_ratio` both return `None` in these cases (`src/insect_variance_protocol.py`) — the series is flagged, not silently coerced to 0, 1, or infinity, and is excluded only from *that specific metric's* model, never from the eligible-series table itself. |
| **unit dependence** | None of the three candidates, nor `CV`, depends on the physical unit abundance is recorded in — this is exactly the scale-invariance result above, restated for units rather than an abstract constant `c`. |
| **monotonic transformations** | Power-mean ratios and quantile ratios are **not** invariant to arbitrary monotonic transforms (e.g. `log`) — only to *multiplicative* rescaling. `D_{3/1}(log1p(x))` is a mathematically different, not equivalent, statistic from `D_{3/1}(x)`. The frozen protocol computes all three candidates on the **raw early-window `Number` scale**, never on the `log1p`-transformed scale used for the trend/outcome computation — mixing the two would silently change what "tight constraint" means without re-deriving the invariance property above. This is stated explicitly so a future round cannot substitute one for the other without re-auditing. |
| **log-transform behavior of the trend/outcome pipeline specifically** | The *outcome* (`docs/HYPOTHESIS_PROTOCOL.md`) is a slope of `log1p(Number)` vs. `Year`, chosen precisely because a slope on raw abundance is not scale-invariant across studies (a study reporting counts 100x larger would mechanically produce a 100x larger raw slope for an identical proportional trend) while a slope of `log1p(x)` approximates a proportional (percent-per-year) trend, which *is* comparable in direction and rough magnitude across differently-scaled studies. `log1p` (rather than plain `log`) is used specifically because `Number` contains exact zeros (2,242 of 61,910 non-missing abundance rows corpus-wide, ~4.0% -- confirmed in `results/DATA_ADEQUACY_AUDIT.md`), and `log(0)` is undefined while `log1p(0) = 0`. |

## Summary

All three frozen constraint candidates and the conventional `CV` baseline
belong to the same invariance class (invariant to positive multiplicative
rescaling), so none of them can, by construction, recover a spurious
cross-study "signal" that is really just a difference in trapping
intensity or measurement unit. They differ from each other in exactly one
scientifically meaningful way: sensitivity to the extreme tail of the
early-window distribution, ranging from `Q_{90/50}` (most robust) through
`D_{3/1}` to `D_{4/1}` (most tail-sensitive). This is the intended,
disclosed methodological contrast between the three candidates, not
redundancy.
