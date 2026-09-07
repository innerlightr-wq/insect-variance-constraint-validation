# CV-of-CVs metric audit (ROUND 2A, Task 7)

**Technical/mathematical audit only. No robust alternative is tested
against outcome data here — candidates are named for future
consideration only, per this round's explicit instruction.**

## 1. Treatment of zero or near-zero means in individual series

`insect_variance_protocol.coefficient_of_variation` (frozen, Round 0)
already returns `None` — never a coerced 0, `inf`, or `nan` — when a
series' mean is exactly 0 or when fewer than 2 observations exist. In the
real historical CV pool used throughout this round (n=1,129, full
usable-year span per eligible series), **zero series were undefined** —
every eligible series had a positive mean and therefore a defined CV
(`docs/CV_OF_CV_ESTIMATOR_PROPERTIES.md`). A group-level `C_g(t)` would
still need to handle the case where some *constituent* series have an
undefined CV within a shorter historical *window* (rather than the full
span) — this is a real possibility not excluded by the full-span result,
and any future H4 must define whether such a series is dropped from that
window's group or causes the whole window to be flagged inadequate
(a design choice, not resolved here).

## 2. Raw or transformed abundance

Per-series CV, throughout this round and Round 0, is computed on **raw
`Number`**, never `log1p`-transformed — consistent with
`docs/METRIC_PROPERTIES.md`'s own caution that `D_{p/1}` and CV are
computed on the raw scale, distinct from the `log1p` scale used only for
the outcome/trend. This is unchanged here.

## 3. Scale invariance under multiplicative rescaling

Unchanged from `docs/METRIC_PROPERTIES.md`: `CV(c*x) = CV(x)` for any
`c > 0`, proven there, not re-derived. Consequently `C_g(t) =
SD_i(CV_{i,t})/Mean_i(CV_{i,t})` is **also** scale-invariant per series —
if one constituent series happens to be reported on a different raw
abundance scale than another (a real possibility across studies pooled
into one context `g`), that difference cancels out of each series' own CV
before the group-level ratio is even formed. This is a structural
strength of building `C_g(t)` from per-series CVs rather than from pooled
raw abundance values directly.

## 4. Sensitivity to rare spikes

CV weights squared deviations from the mean — less extreme-value-sensitive
than the higher-order `D_{3/1}`/`D_{4/1}` ratios audited in Round 0, but
not robust: a single very large count within one series inflates that
series' own CV, which then propagates into `C_g(t)` exactly as
characterized empirically in Task 6 above (a single extreme *constituent
CV* shifts the group statistic by a large, non-shrinking amount even at
n=30).

## 5. Sensitivity to series length

A series' own CV is a function of its full observed history; a short
historical window (Task 5) gives each constituent series' CV less data to
average over, inflating its own sampling noise before it ever enters
`C_g(t)`. This compounds with item 4 — noisier constituent CVs make the
group statistic's own extreme-sensitivity worse, not merely add
independent noise.

## 6. Sensitivity to missing years

A series with irregular or gapped historical coverage (common in this
corpus — Round 0's schema audit found ~28.4% of plot-stratum-year cells
null after within-year aggregation) contributes a CV computed only from
its *observed* years, silently treating gaps as "not sampled" rather than
as "sampled at zero" — the same, already-frozen, disclosed convention
used throughout Round 0/Round 1 (`aggregate_within_year`'s `min_count=1`
rule). A future `C_g(t)` inherits this convention unchanged; it is not
revisited here.

## 7. Effect of unequal within-window observation counts

Constituent series within the same context/window frequently have
unequal numbers of usable years (Task 3's `median_obs_per_eligible_series`
varies by study). Each series' own CV is still a valid statistic
regardless of exactly how many years it has (as long as `n>=2`), but
series with very few usable years in a given window contribute a
noisier, less precise CV to the group than series with many — `C_g(t)`
as currently defined does **not** weight constituent series by their own
precision. A precision-weighted variant is a candidate for future
consideration (see below) but is not constructed or tested here.

## 8. Whether robust alternatives would be needed — candidates named, none tested

Named for future consideration only, **not tested against any outcome in
this or any prior round**:

- a **trimmed** or **winsorized** version of `C_g(t)` (dropping or capping
  the single most extreme constituent CV before computing the group
  ratio) — directly motivated by Task 6's finding that one extreme value
  dominates even at n=30;
- a **precision-weighted** group statistic, weighting each constituent
  series' CV by its own inverse variance or by its usable-year count —
  directly motivated by item 7 above;
- a **median-based** dispersion-of-dispersions statistic (e.g.
  `IQR(CV_i)/Median(CV_i)`) as a robust alternative to `SD/Mean`.

**None of these is constructed, computed, or compared to any outcome in
this round.** They are recorded here so a future, separately-frozen round
does not have to rediscover them, and so that if one is eventually
adopted, it is visibly traceable to a feasibility-stage observation, not
introduced after seeing a weak or favorable result.
