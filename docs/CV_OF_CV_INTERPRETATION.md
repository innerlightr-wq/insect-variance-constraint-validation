# CV-of-CVs interpretation audit (Task 15)

**This is a mathematical/interpretive audit of what a dataset-level
dispersion-of-dispersions statistic can and cannot establish. It is not a
test of H1/H2/H3 and does not touch the future outcome variable at all —
`CV_CVs` is computed purely from each series' own within-series values,
with no reference to any later period or any predictor-outcome
relationship.**

## What the manuscript reports, and what this repository independently found

The manuscript reports `CV_CVs ≈ 0.610`, described as `SD(plot CVs) /
Mean(plot CVs)`. **This repository does not accept that figure or its
"bounded distribution" interpretation automatically.**

An independent computation from the checksum-verified raw data (all 1,613
candidate abundance series, i.e. `(DataSource_ID, Plot_ID, Stratum)` with
`MetricAB == "abundance"`, full usable-year span per series, `CV = SD /
mean` on the raw `Number` scale, sample SD with `ddof=1`) gives:

```
mean(series CV)   = 0.736
sd(series CV)     = 0.377
CV_of_CVs         = 0.512
median(series CV) = 0.675
range(series CV)  = [0.0, 4.0]
```

**This is in the same general range as the manuscript's ~0.610 but is not
an exact reproduction.** Plausible sources of the difference, disclosed
rather than resolved by guessing: this repository's own frozen
within-year aggregation rule (sum across periods, §`docs/HYPOTHESIS_PROTOCOL.md`)
may not match whatever rule the original analysis used; the exact
population of series/plots included may differ (e.g. a different minimum
series-length filter, or a different treatment of the 175 plots with more
than one `(Stratum, MetricAB)` combination); and the original code was not
available to this project (`ReadMe.docx` was not downloaded this round —
see `docs/DATA_PROVENANCE.md`). **This is not treated as a discrepancy
that matters for the argument below** — the interpretive limits of a
CV-of-CVs statistic do not depend on whether its value is 0.51 or 0.61.

## What a finite CV-of-CVs value mathematically establishes

Four claims must be kept strictly separate. `CV_CVs` (any finite value)
establishes claim 1 only, by itself:

1. **Finite empirical dispersion.** A finite, computable value simply
   means the sample of per-series CVs has a finite mean and a finite
   standard deviation. This is true of essentially *any* real, finite
   empirical dataset — it is close to a tautology, not a substantive
   ecological finding. **`CV_CVs` alone establishes only this.**

2. **Sampling uncertainty.** A specific numeric value (0.51, 0.61, or any
   other) computed from a finite sample (1,613, or however many, series)
   is itself an estimate with sampling variability. A bootstrap confidence
   interval around it would quantify *how precisely this sample's own
   CV-of-CVs is known* — it says nothing about the underlying
   population beyond ordinary estimation uncertainty.

3. **Evidence of an ecological upper bound.** This is a **qualitatively
   different claim** — that some biological or physical mechanism caps how
   variable an insect population's abundance can be. **A finite empirical
   CV-of-CVs, with or without a bootstrap CI, does not establish this.**
   To argue for a genuine bound, one would need to show the *distribution*
   of per-series CVs is inconsistent with an unbounded generating process
   (e.g. a heavy-tailed distribution with no natural ceiling) — not merely
   that the empirically observed dispersion is a specific finite number.
   A CV-of-CVs is a two-number summary (mean and SD of one distribution);
   it cannot, by itself, distinguish "the true underlying process is
   bounded" from "the true underlying process is unbounded but this
   particular finite sample of ~1,600 series, drawn from ~99-166 specific
   studies with their own specific trapping methods and durations, happens
   to have a moderate empirical spread." The observed range in this
   repository's own computation (series CV from 0.0 to 4.0) shows real,
   substantial variation across four orders of magnitude of relative
   scale even within this one finite sample — consistent with either a
   bounded or an unbounded generating process.

4. **Evidence of predictive value.** This is the claim this project's own
   H1/H2 are designed to test, and `CV_CVs` — a single, dataset-level,
   backward-looking descriptive number — **cannot possibly establish it**,
   for a structural reason, not merely an empirical one: `CV_CVs` is not
   even defined per-series (it is one number for the whole dataset), so it
   has no way to vary across series and therefore cannot predict which
   *specific* series will decline more than another. This is exactly why
   Task 7 requires the frozen per-series constraint metrics (`D_{3/1}`,
   `D_{4/1}`, `Q_{90/50}`) instead of `CV_CVs` itself as H1/H2's
   predictors — they are computed within each series, `CV_CVs` is not.

## A proper null/reference test, if one is scientifically meaningful (proposed, NOT executed)

If a future round wanted to test claim 3 (an ecological bound) rather than
merely describe claim 1, a defensible design would compare the empirical
distribution of per-series CVs against a reference null generated from a
model with **no** upper bound on variability (e.g. a log-normal or
Pareto-tailed generative model for per-series abundance variance,
calibrated to match this dataset's own sample sizes and mean, then checked
for whether the empirical CV distribution's tail is significantly lighter
than that null would produce). **This is explicitly proposed here as a
separately-frozen SECONDARY test for a future round, not executed in this
round, and not part of the primary H1/H2/H3 Holm family**
(`docs/HYPOTHESIS_PROTOCOL.md` §10). It requires its own freeze document,
its own predeclared null model, and its own STOP conditions before any
execution.

## Conclusion

`CV_CVs`, at whatever exact value, is a legitimate descriptive fact about
this dataset (claim 1), carries ordinary sampling uncertainty like any
other finite-sample statistic (claim 2), and **is not, by itself, evidence
of an ecological upper bound on population variability (claim 3) nor of
any predictive value for future decline (claim 4)**. This project's
primary hypotheses (H1/H2) do not rely on `CV_CVs` or on claim 3 at all —
they are tested exclusively through the per-series constraint metrics
frozen in `docs/HYPOTHESIS_PROTOCOL.md`.
