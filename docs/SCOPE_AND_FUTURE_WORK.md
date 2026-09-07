# Scope and future work

## PRIMARY (this repository, this round and the primary hypothesis round that follows it)

**Long-term insect abundance validation**: H1 (out-of-sample constraint
hypothesis), H2 (incremental information hypothesis), and — only where
the frozen stratum gate permits (`docs/HYPOTHESIS_PROTOCOL.md` §6) — H3
(ecological-stratum moderation), tested against the van Klink et al.
(2020) global insect assemblage database (`docs/DATA_PROVENANCE.md`).

## FUTURE (explicitly out of scope for the primary hypothesis test; not executed, not tested, not assumed)

- **Independent insect replication** — cross-checking H1/H2 against a
  second, independently-sourced long-term insect monitoring dataset, to
  test whether any supported result generalizes beyond this one corpus.
- **Bioacoustic monitoring extension** — the manuscript's Cicadidae/
  Orthoptera bioacoustic material. **Not included in the primary
  validation.** No bioacoustic dataset has been downloaded, inspected, or
  referenced by any code or claim in this repository.
- **Paleontological cross-scale analogy** — the manuscript's Paleozoic
  chondrichthyan comparison. **Not included in the primary validation.**
  No paleontological dataset or claim is referenced anywhere in this
  repository. Cross-scale claims (insect ecology vs. deep-time vertebrate
  diversification) are not tested, assumed, or gestured at in this round
  or the round that follows it.

Both future extensions require their own, separately frozen provenance,
schema audit, and hypothesis protocol before any code touches them — the
same discipline applied to the primary dataset in this round. Nothing in
`docs/HYPOTHESIS_PROTOCOL.md`'s H1/H2/H3 depends on either extension.

## Taylor's Law — benchmark/descriptive replication only, not evidence for H1/H2

The manuscript reports an approximate Taylor's Law fit (`variance ~
a*mean^b`) with `b ≈ 1.96`, `R² ≈ 0.96`. **These values are not assumed
correct here.**

**Status in this repository: not yet executed.** A reproducible
replication is planned (log-log OLS of within-series variance against
within-series mean, computed per eligible series on the same raw
`Number` scale used throughout, across the full usable-year span of each
series — a separate computation from the early/late split used for
H1/H2), but is **explicitly kept analytically separate from H1 and H2**:

- Taylor's Law describes a **population-level scaling relationship**
  between mean and variance across many series at one point in time (a
  purely descriptive, backward-looking regularity of this dataset).
- H1/H2 test **prospective, out-of-sample predictive information** in one
  specific early-window statistic about one specific series' own later
  outcome.
- A high Taylor's Law `R²` would say this dataset's mean-variance scaling
  is regular and well-described by a power law — **it would not, by
  itself, say anything about whether any constraint metric predicts
  future decline.** These are conflated in casual reading of the
  manuscript; they are not conflated here.

When executed (a future, separately-committed step, not part of this
freeze), the replication's exponent and R² will be reported as a
benchmark/descriptive fact about this corpus, explicitly labeled as not
bearing on H1/H2's support or failure either way.
