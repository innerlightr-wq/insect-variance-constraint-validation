# insect-variance-constraint-validation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22646397.svg)](https://doi.org/10.5281/zenodo.22646397)

**Independent computational validation project.** This is the living
computational/reproducibility record for the permanently archived
manuscript below; see [Citation](#citation) for the archived version of
record. This repository tests
the hypothesis that constrained historical variance structure may predict
subsequent insect community deterioration beyond variance magnitude alone
— the central claim of the manuscript *"Variance Constraints, Not
Variance Magnitude, as Indicators of Insect Community Vulnerability:
Evidence from Long-Term Insect Abundance Monitoring"* (Elias De Jesús,
Independent Researcher, ORCID 0009-0007-0190-9143).

It follows the same research discipline as this author's
`linear-a-constraint-validation` project: prospective hypothesis freeze,
explicit provenance, exact inclusion/exclusion rules, blocked (grouped)
validation, predeclared negative controls, and preservation of negative
results.

## Citation

De Jesús, Elias. (2026). *Variance Constraints Do Not Improve Prediction
of Subsequent Insect Abundance Change: A Prospective Validation Across
Long-Term Monitoring Studies.* Zenodo.
[https://doi.org/10.5281/zenodo.22646397](https://doi.org/10.5281/zenodo.22646397)

This GitHub repository (`insect-variance-constraint-validation`) is the
living, version-controlled computational record — frozen protocols,
execution code, tests, and results — underlying the manuscript above.
The Zenodo DOI is the permanent archival deposit and citable version of
record; see `manuscript/insect_variance_constraint_validation_revised.pdf`
for the manuscript itself.

## What this is

- **Validation-oriented**, not confirmation-oriented: the goal is to let
  the hypothesis survive, weaken, or fail against independently-verified
  data, not to demonstrate it is true.
- **Prospective**: the primary outcome, eligibility rules, predictors,
  validation design, and negative controls are all frozen — committed to
  this repository — **before** any predictor-outcome association is
  computed. See `docs/HYPOTHESIS_PROTOCOL.md`.
- **Preserving of negative results**: a clean, well-powered null result is
  a valid, reportable outcome of this protocol, not a failure of the
  project.

## The actual hypothesis under test

The central claim is **not** "low variance means vulnerability" and **not**
"some ecological strata have lower dispersion than others." It is:

> Does constrained historical variance structure, measured in an EARLY
> window, contain out-of-sample information about a LATER ecological
> outcome, beyond ordinary variance magnitude, prior trend, and study
> structure?

`constraint strength != target-specific predictive information` — a tight
variance regime is scientifically interesting here only if it predicts a
later outcome after conventional predictors are controlled, exactly the
same conceptual discipline this author's Linear A project's
constraint-information-mechanism round established for a different domain
(`constraint != state-space reduction != target-specific information`).

## Key methodological commitments

- **Cross-study abundance levels are not assumed directly comparable.**
  All candidate constraint metrics are scale-invariant by construction
  (proven, not assumed — `docs/METRIC_PROPERTIES.md`) precisely because
  abundance is recorded on incommensurable raw scales across ~99-166
  different original studies.
- **Prediction is evaluated strictly within each longitudinal series**:
  every series contributes its own early-window predictors and its own
  late-window outcome — never pooled across series as if they were
  comparable absolute levels.
- **Grouped (study-aware) validation prevents study leakage**: all series
  from the same source study are always assigned to the same
  cross-validation fold (`docs/HYPOTHESIS_PROTOCOL.md` §7) — random
  row-wise cross-validation is explicitly prohibited.

## Primary dataset

van Klink, R., et al. (2020). *A global database of long-term changes in
insect assemblages.* Knowledge Network for Biocomplexity.
DOI: [10.5063/F11V5C9V](https://doi.org/10.5063/F11V5C9V). CC BY 4.0. Full
provenance, checksums, and independent verification of the manuscript's
own scale claims: `docs/DATA_PROVENANCE.md`. **No raw data is committed to
this repository** — see `data/README.md` to rebuild it locally.

## Research status

```
ROUND 0: DATA / DESIGN / PROTOCOL FREEZE — COMPLETE

H1 (out-of-sample constraint hypothesis):  NOT YET TESTED
H2 (incremental information hypothesis):   NOT YET TESTED
H3 (ecological-stratum moderation):        NOT YET TESTED

Power/adequacy gate (Task 18): READY
  1,129 eligible series across 99 studies (data/raw/insect_knb,
  checksum-verified). See results/POWER_ADEQUACY_AUDIT.md.
```

**No hypothesis test, model fit, coefficient, or p-value against the
primary outcome exists anywhere in this repository as of this freeze.**
`results/POWER_ADEQUACY_AUDIT.md` and `results/DATA_ADEQUACY_AUDIT.md`
report only structural facts about the data and the outcome variable's own
marginal distribution — never any predictor-outcome association.

## Repository structure

```
docs/      frozen protocols, provenance, mathematical audits
src/       reusable pipeline code (power means, eligibility, folds, controls)
tests/     unit + data-integration tests (pytest)
data/      raw/processed data — gitignored; see data/README.md
results/   audit reports (schema, power/adequacy) — machine + human readable
```

Frozen protocol documents: `docs/DATA_PROVENANCE.md`,
`docs/ANALYSIS_UNIT.md`, `docs/METRIC_PROPERTIES.md`,
`docs/HYPOTHESIS_PROTOCOL.md`, `docs/CV_OF_CV_INTERPRETATION.md`,
`docs/SCOPE_AND_FUTURE_WORK.md`.

## Reproducing Round 0

```bash
pip install -r requirements.txt   # pandas, numpy, scipy, scikit-learn, pytest
# fetch the raw corpus -- see data/README.md for exact commands + checksums
python3 src/audit_dataset.py
python3 src/power_adequacy_audit.py
pytest    # 46 tests as of this freeze (some skipped automatically if the
          # raw corpus has not been fetched locally)
```

## Scope

**Primary, this round and the hypothesis-test round that follows it:**
long-term insect abundance validation (H1/H2, and H3 where the frozen
stratum gate permits).

**Explicitly out of scope, not touched by any code or claim here:**
independent insect replication, a bioacoustic monitoring extension, and a
paleontological cross-scale analogy. See `docs/SCOPE_AND_FUTURE_WORK.md`.
Taylor's Law is planned only as a separate descriptive benchmark, never as
evidence for or against H1/H2.

## License

- **Software** (`src/`, `tests/`): not yet finalized. The repository is
  publicly hosted, but no license has been chosen for this code yet — do
  not assume any particular license until one is explicitly added.
- **Research documentation and computational results** (`docs/`,
  `results/`, this README): same status — not yet finalized.
- **Third-party data**: the primary dataset (van Klink et al. 2020) is CC
  BY 4.0 (see `docs/DATA_PROVENANCE.md`); this repository does not commit
  it and does not claim to relicense it.

## Author

Elias De Jesús, Independent Researcher. ORCID:
[0009-0007-0190-9143](https://orcid.org/0009-0007-0190-9143).
