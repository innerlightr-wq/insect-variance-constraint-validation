# Analysis unit

**Frozen unit of analysis:** a longitudinal series keyed by
**`(DataSource_ID, Plot_ID, Stratum)`**, restricted to `MetricAB ==
"abundance"` (Task 5 — abundance is the primary analysis; biomass series,
keyed identically, are reserved for a separate sensitivity analysis and
never pooled with abundance series). Implemented as `SERIES_KEY` in
`src/insect_variance_protocol.py`.

## Why this key, and not something coarser or finer

- **`Plot_ID` alone is insufficient**, in principle, because a single
  physical plot can be monitored across more than one ecological stratum
  (e.g. both `Air` and `Soil surface` insects at the same site) and,
  occasionally, both `abundance` and `biomass`. Verified directly from the
  real data: **175 of 1,663 plots** have more than one distinct
  `(Stratum, MetricAB)` combination recorded
  (`results/data_adequacy_audit.json`, computed during schema audit).
  Treating all of a plot's stratum-specific records as one series would
  silently average across ecologically distinct sub-communities that the
  source itself treats as separate observational streams.
- **`DataSource_ID` is included in the key even though it is empirically
  redundant with `Plot_ID`** in this specific corpus: every `Plot_ID` in
  `InsectAbundanceBiomassData.csv` maps to exactly one `DataSource_ID` in
  `PlotData.csv`, with **zero cross-table mismatches** (verified in
  `results/DATA_ADEQUACY_AUDIT.md`, referential-integrity section). It is
  kept in the key anyway because (a) it is the field the frozen grouped
  cross-validation (Task 10) groups on, and code that constructs the
  series key should use the same field the fold logic uses, not a
  field that merely happens to correlate with it; (b) it protects against
  a hypothetical future corpus update where `Plot_ID` uniqueness across
  studies is no longer guaranteed.
- **`Stratum` is part of the key** for the reason given above: strata are
  ecologically distinct assemblages (Air / Water / Herb layer / Soil
  surface / Trees / Underground), and pooling them at the plot level would
  average across community types the data source itself already
  distinguishes.
- **`MetricAB` is not part of the frozen primary key** — it is filtered to
  `"abundance"` *before* the key is ever constructed (Task 5's own
  instruction), rather than being included as a fourth key component that
  would need to be reconciled with a differently-scaled biomass series
  later. This is a deliberate simplification: it means the sensitivity
  analysis (biomass) reruns the *entire* pipeline on a `MetricAB ==
  "biomass"` filtered table using the identical `(DataSource_ID, Plot_ID,
  Stratum)` key, rather than trying to make one combined key do both jobs.

## Pseudo-replication

Each row of `InsectAbundanceBiomassData.csv` is one (study, plot, stratum,
metric, sampling period, year) observation — **not** independent across
years within a series (by construction, it is the same physical plot
sampled repeatedly), and **not** independent across series within the same
study (shared methodology, shared observers, shared regional
environmental drivers). Two dependence structures are therefore handled,
never conflated:

1. **Within-series (across years):** handled by treating the series
   itself, not the individual year-observation, as the unit that
   contributes one early-window feature vector and one late-window
   outcome value to any future model. A series contributes exactly one
   row to any future H1/H2 modeling table, never one row per year.
2. **Across-series, within-study:** handled by the frozen grouped
   cross-validation (`docs/HYPOTHESIS_PROTOCOL.md`, Task 10) — all series
   sharing a `DataSource_ID` are always assigned to the same fold, so no
   fold ever trains on part of a study and tests on another part of the
   same study.

## Taxonomy / treatment splits

`ExperimentalTreatment` is present in `PlotData.csv` (confirmed,
`results/DATA_ADEQUACY_AUDIT.md`) but is **not** incorporated into the
series key this round. It is left as a documented, unresolved
disambiguation question: if a single `Plot_ID` in fact contains pooled
treatment and control sub-plots under one plot identifier (as opposed to
each treatment arm already having its own distinct `Plot_ID` — which the
source's structure suggests, since `ExperimentalTreatment` is a per-plot
attribute in `PlotData.csv`, not a per-observation attribute in
`InsectAbundanceBiomassData.csv`), no further split is needed. This is
recorded as an open item for a future round to re-verify against
`PlotData.csv`'s own documentation (`ReadMe.docx`, not downloaded this
round — see `docs/DATA_PROVENANCE.md`), not resolved by assumption here.
Taxonomic splitting below `Stratum` (e.g. by `InvertebrateGroup` in
`DataSources.csv`) was considered and rejected for the primary series key,
because `InvertebrateGroup` is recorded at the *study* level, not
per-observation, and splitting on it would not, by itself, separate
anything `Stratum` does not already separate within a single study.
