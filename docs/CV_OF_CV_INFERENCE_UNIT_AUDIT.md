# CV-of-CVs pseudoreplication / unit-of-analysis audit (ROUND 2A, Task 9)

**This is the most important document in this round.** Getting the
inferential unit wrong here would silently manufacture statistical power
that does not exist — exactly the failure mode Round 0's own
`docs/ANALYSIS_UNIT.md` was written to prevent for the individual-series
predictors, now recurring one level up for a group-level predictor.

## What the eventual inferential unit could defensibly be

`C_g(t)` is, by construction, **one number per (context, historical
window)** — it does not vary by plot or by individual series within that
context/window. Three candidate inferential units, assessed structurally:

1. **Study-level**: one `C_g(t)` value (or one LEVEL/CHANGE summary) per
   `DataSource_ID`, tested against... what outcome? A study has no single
   outcome — it contains many eligible series, each with its own
   late-window outcome (Round 1's frozen target). Using study-level alone
   would require first collapsing all of a study's outcomes into one
   number (e.g. mean future trend), discarding all within-study outcome
   variation — a large loss of information, and a different, new outcome
   definition Round 1 never froze.
2. **Study-window level**: one `C_g(t)` per (study, historical window) —
   the natural unit `C_g(t)` is actually defined at. Still faces the same
   problem as (1) if paired against a single collapsed future outcome.
3. **Series level, with a study-window-level predictor broadcast onto
   each series**: assign the *same* `C_g(t)` value to every one of a
   study's eligible series (each retaining its own individual future
   outcome from Round 1). **This is the only option that preserves
   Round 1's own outcome definition and sample**, but it is exactly the
   pseudoreplication risk this task explicitly warns against.

## The pseudoreplication warning, made concrete with this round's own numbers

If option 3 were used naively — treating each of a study's plots as an
independent predictor observation, all sharing one broadcast `C_g(t)`
value — the *effective* number of independent predictor observations is
the **number of studies with an adequate window (38, Task 8 LEVEL
feasibility)**, not the number of series those studies contain (**1,019
series**, Task 3's threshold-5 row). Fitting any model as if it had 1,019
independent predictor observations when the predictor genuinely only
varies at 38 independent points would be a severe, not a minor,
inferential error — the same category of mistake Round 0's own grouped
cross-validation and study-clustered standard errors were built
specifically to prevent for series-level predictors, now recurring with a
much smaller effective N (38, not 99) because the predictor is even
coarser than `DataSource_ID` alone (it also requires window adequacy).

**Any future H4 MUST cluster or group by, at minimum, `DataSource_ID`,
exactly as Round 1 already does — and must additionally treat the
EFFECTIVE sample size for any inference ABOUT the predictor's own
between-context variation as the number of adequate (context, window)
units (38 for LEVEL, 14/4/3 for CHANGE at >=3/4/5 windows — Task 8), not
the number of series or plots those contexts happen to contain.** A
model that reports "n=1,019" as its sample size for a claim about
`C_g(t)`'s effect would be self-evidently misleading given these numbers.

## Repeated windows within studies (CHANGE)

Task 8's CHANGE feasibility already quantifies this: only 14 of 99
studies have `>=3` sequential adequate 10-year windows, dropping to 4 at
`>=4` and 3 at `>=5`. **Windows within a study are not independent of one
another** even where they exist — they share the same underlying set of
plots and the same study's own methodology, so a within-study CHANGE
slope has, at best, only as many independent-ish points as it has
adequate windows (typically 3), an extremely thin basis for a
per-study trend estimate. A pooled (cross-study) CHANGE analysis would
therefore itself need to be a two-level model (windows nested in
studies) or use study-clustered inference on the CHANGE slope — never
treat within-study windows as independent observations.

## Whether multiple strata within a study are independent enough to separate

Not audited to full independence in this round (would require a stratum
x study x window three-way breakdown beyond this round's scope), but the
same caution applies directly: if a future H4 computes `C_g(t)` separately
per `(DataSource_ID, Stratum)` rather than per `DataSource_ID` alone (a
finer context, considered in `docs/CV_OF_CV_EARLY_WARNING_CONCEPT.md`
item 3), the group sizes feeding each `C_g(t)` shrink further — this
would need its own Task 3-style support audit before being adopted, not
assumed adequate by extension from the study-level numbers above.

## Conclusion for Task 13

The defensible inferential unit for a future H4 is **the (study,
historical-window) pair**, evaluated with study-level clustering/grouping
(never plot- or series-level as the unit of independent replication), and
with the EFFECTIVE N for any claim about the predictor's own explanatory
power reported as the number of adequate context-windows (order of
dozens: 38 for LEVEL), not the number of series broadcast onto them
(order of a thousand). This constraint is carried into Task 13's
recommendation below.
