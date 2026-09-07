# Final revision notes

## Original exploratory hypothesis

The original manuscript (`docs/ORIGINAL_MANUSCRIPT_PROVENANCE.md`,
`~/Downloads/EcologicalEntomology.pdf`) proposed that higher-order
variance structure — particularly a bounded population-level CV-of-CVs
(reported $\approx 0.610$) and stratum-specific "depth ratio" contrasts
($D_{3/1}$) — could diagnose ecological vulnerability independent of, and
in some cases opposite to, raw variance magnitude. It proposed the Herb
layer and Soil surface as candidate vulnerability bottlenecks, Air and
Water as candidate buffers, and four exploratory early-warning metrics
(CV-of-CVs deviation, depth-ratio collapse, Taylor-exponent shift,
year-over-year ratio clustering). It explicitly called its own findings
diagnostic, correlational, and in need of validation on independent data
and prospective time series before any indicator could be treated as
established.

## Round 0: prospective freeze

A wholly separate, later research program took that call for validation
literally. Round 0 (`21e6992`) froze — before any predictor-outcome
association was computed — the eligible-series construction, the
chronological early/late split, the primary outcome definition, three
scale-invariant constraint-metric candidates ($D_{3/1}$, $D_{4/1}$,
$Q_{90/50}$), the conventional baseline, the grouped validation design,
three negative controls, and the Holm multiplicity family.

## Round 1: negative result

Round 1 (`206742f`) executed that frozen protocol exactly once. All three
individual constraint metrics failed (wrong direction, Holm $p=1.000$,
$1.000$, $0.171$). The incremental-value test (H2) — the manuscript's
actual title claim — failed identically (M1 RMSE slightly worse than M0,
Holm $p=1.000$, both negative controls consistent with chance). Secondary
stratum tests found no consistent direction across Air/Water/Herb
layer/Soil surface, with constraint metrics making prediction materially
*worse* in Herb layer and Soil surface specifically — the two strata the
original manuscript singled out as bottlenecks.

## Round 2A: feasibility audit

Rather than treat the original CV-of-CVs claim as simply refuted by
implication, a separate feasibility question was asked: could a
*contextual*, time-varying version of CV-of-CVs even be defined
prospectively from this data, strongly enough to test? Round 2A
(`d3246d9`) audited this without ever touching any outcome value, finding
LEVEL marginally feasible, CHANGE clearly underpowered, and identifying
$n\geq15$ constituent series and the (study, historical-window) pair as
the correct minimum adequacy bar and inferential unit.

## H4: independent freeze and negative result

That recommendation was converted into an immutable protocol (`3e30670`)
and executed exactly once (`8d6db88`). Effective study $N$ came in at 11
(not the feasibility round's own $\sim$19–20 estimate — that estimate
predated a temporal-eligibility filter the H4 freeze itself derived).
The result: no incremental predictive value ($\Delta$RMSE $=-0.002354$,
permutation $p=0.5304$). NOT SUPPORTED.

## Claims removed

Vulnerability-predictive framing for $D_{3/1}$, $D_{4/1}$, $Q_{90/50}$,
and CV-of-CVs; the Herb-layer/Soil-surface bottleneck and Air/Water
buffer interpretations; universal-constant/ecological-bound framing for
CV-of-CVs; the four exploratory early-warning-metric proposals (CV-of-CVs
deviation, depth-ratio collapse, Taylor-exponent shift, year-over-year
clustering) as validated indicators; specific conservation-prioritization
recommendations; the paleontological and bioacoustic material as
supporting evidence for the primary mechanism; causal-sounding language
("propagate," "amplify," "transmit") describing an untested mechanism.

## Claims retained

Dataset scale and provenance (70,955 observations, 1,663 plots, 166
studies, 1925–2018); Taylor's Law as a strong descriptive replication
(retained, with updated validated values $b=1.930$, $R^2=0.974$, rather
than the original's $b\approx1.959$, $R^2\approx0.962$); the general
literature motivating why higher-order variance structure was worth
testing in the first place (background only, not conclusions); CV-of-CVs
as a legitimate, real, *contextual* descriptive/measurable quantity (this
is the one claim H4 itself affirmatively demonstrates); the original
manuscript's own epistemic caution (its Epistemic Status and Limitations
sections already disclaimed causality and universality — this revision
honors, rather than contradicts, that original caution).

## Why the title changed

The original title asserted the paper's central positive claim directly
("Variance Constraints, Not Variance Magnitude, as Indicators of Insect
Community Vulnerability"). That claim is the one this validation program
tested and did not support (Round 1 H2, `206742f`). A title asserting it
would misrepresent the paper's own results. The new title states the
actual finding directly: constraint metrics did not improve prediction,
under a prospective, multi-study validation.

## Why CV-of-CVs is now described as contextual

The original manuscript already, correctly, called its own
$\mathrm{CV}_{\mathrm{CVs}}=0.610$ estimate "a dataset-specific diagnostic
metric rather than a universal ecological constant" — this revision does
not weaken that caution, it enforces it consistently everywhere the
statistic is discussed, and extends it into H4's own predictor design:
$C_g$ is defined, by construction, per study, and H4 tests only whether
*variation* in $C_g$ across studies carries prospective information —
never whether any single value of $C_g$ (or the global $\mathrm{CV}_{\mathrm{CVs}}$)
is universal.

## Why the revision was deliberately delayed until all frozen prospective tests were completed

Revising the manuscript after Round 1 alone, but before Round 2A/H4, would
have left the CV-of-CVs claims addressed only by implication (Round 1
never tested CV-of-CVs at all — it tested $D_{3/1}$, $D_{4/1}$,
$Q_{90/50}$). Writing the "final" negative-results paper before H4
existed would have required either silently dropping the CV-of-CVs claims
without a test, or leaving them in an unrevised, unsupported state. The
manuscript revision was held until H4 — the specific, independently
frozen prospective test of contextual CV-of-CVs — was itself complete, so
that every major claim in the original manuscript could be classified
against an actual, frozen, executed result rather than against an
inference from a different test.

## Provenance commits used

`21e6992` (Round 0 protocol freeze), `206742f` (Round 1 results),
`d3246d9` (CV-of-CVs feasibility audit), `3e30670` (H4 protocol freeze),
`8d6db88` (H4 results). No commit in this chronology was reopened,
modified, or reinterpreted by this revision. No new hypothesis analysis
was run to produce this manuscript; all numbers were read from the
already-committed result files listed in `docs/FINAL_MANUSCRIPT_CLAIM_CROSSWALK.md`.
