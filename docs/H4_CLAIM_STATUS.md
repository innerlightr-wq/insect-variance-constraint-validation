H4 FROZEN PROTOCOL COMMIT: 3e30670
PARENT FEASIBILITY COMMIT: d3246d9

# H4 claim status

| # | claim | status | basis |
|---|---|---|---|
| 1 | CV-of-CVs is measurable contextually | **SUPPORTED** | `C_g` was computed for 16 structurally-adequate `(study, 10-year window)` units (11 with at least one usable future-outcome-eligible series), from real, checksum-verified data, with zero leakage violations (`results/H4_LEAKAGE_AUDIT.md`, 384/384 checks clean). |
| 2 | CV-of-CVs is a universal constant | **NOT SUPPORTED** | Never claimed or tested as such anywhere in this project. `docs/CV_OF_CV_INTERPRETATION.md` (Round 0) already showed a finite empirical value establishes nothing about universality; H4 itself tests only *variation* in a *contextual* `C_g` across studies (`docs/H4_PROTOCOL.md` Sec.6), never a single global value. |
| 3 | CV-of-CVs is an ecological bound | **NOT SUPPORTED** | Same basis as #2 — `docs/CV_OF_CV_INTERPRETATION.md`'s four-way distinction (finite dispersion / sampling uncertainty / ecological bound / predictive value) is unchanged; nothing in H4 bears on the "bound" claim specifically. |
| 4 | historical CV-of-CVs predicts later abundance change | **NOT SUPPORTED** | H4 primary result: pooled LOSO delta RMSE = -0.002354 (M1 slightly *worse* than M0), one-sided permutation p = 0.5304 (n=10,000, seed 20260907) — `results/H4_PRIMARY_RESULTS.md`, `results/H4_PERMUTATION_RESULTS.md`. |
| 5 | historical CV-of-CVs adds information beyond conventional baseline predictors | **NOT SUPPORTED** | This is exactly H4's primary (H2-style) test — same result as #4; the frozen support rule (`delta_rmse > 0 AND p <= 0.05`) is not met. |
| 6 | CV-of-CVs is an established early-warning indicator | **NOT SUPPORTED** | Directly false given #4-5, and additionally barred as an overclaim under `docs/H4_INTERPRETATION_BOUNDARIES.md` regardless of any single H4 result — a `SUPPORTED` outcome would still not license "established" (that requires deployment/validation this project's design cannot provide). |
| 7 | temporal CHANGE in CV-of-CVs is an early-warning indicator | **UNDERPOWERED** | Never tested — explicitly excluded from H4 by the frozen protocol (`docs/H4_PROTOCOL.md` Sec.2, "No secondary CHANGE test may be run after H4"). Round 2A found only 14/4/3 studies at >=3/4/5 sequential adequate windows (`results/CV_OF_CV_LEVEL_VS_CHANGE.md`) — inadequate at any reasonable multiplicity. |

**Summary: 1 SUPPORTED (measurability only), 5 NOT SUPPORTED, 1 UNDERPOWERED (CHANGE, untested by design).**
No claim in this table is overstated relative to `results/H4_VERDICT.md`'s primary finding (`NOT SUPPORTED`) or `docs/H4_INTERPRETATION_BOUNDARIES.md`'s standing limits.
