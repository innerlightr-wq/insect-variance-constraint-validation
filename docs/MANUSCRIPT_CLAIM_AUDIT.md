FROZEN PROTOCOL COMMIT: 21e6992

# Manuscript claim audit

**Round 1 primary result: NEGATIVE UPDATE** (`results/ROUND1_VERDICT.md`).
This audit classifies each major manuscript claim against what Round 0/
Round 1 actually tested, computed, or left untouched. **Claims are not
preserved merely because they appeared in the original manuscript** — see
each classification's basis, cited to the specific result file or the
specific absence of a test.

| # | claim | classification | basis |
|---|---|---|---|
| 1 | `CV_CVs ≈ 0.610` | **DESCRIPTIVE ONLY** | Independently recomputed at 0.512 (`results/round1_descriptive_benchmarks.json`, same methodology as `docs/CV_OF_CV_INTERPRETATION.md`) — same general range, not an exact reproduction (original code/exact filtering unavailable, disclosed in Round 0). A finite CV-of-CVs value is a legitimate descriptive fact about this corpus and nothing more. |
| 2 | "bounded distribution" interpretation of CV_CVs | **NOT SUPPORTED** | No test of an ecological upper bound was performed or licensed — `docs/CV_OF_CV_INTERPRETATION.md` shows this interpretation does not follow from a finite CV-of-CVs value by itself, and no reference-null test for boundedness was executed (one was only proposed, as an explicitly separate future secondary test). |
| 3 | Herb layer as vulnerability bottleneck | **NOT SUPPORTED** | H3 (secondary, uncorrected — `results/ROUND1_STRATUM_RESULTS.md`): Herb layer's constraint-metric coefficients all point OPPOSITE the frozen H1 direction, and adding constraint metrics made out-of-sample prediction substantially worse there (M0 RMSE 0.257 -> M1 RMSE 0.298, ΔRMSE = -0.041, the largest degradation of any tested stratum). No pattern here supports singling out Herb layer as a constraint-driven bottleneck. |
| 4 | Soil surface as vulnerability layer | **NOT SUPPORTED** | H3 (secondary, uncorrected): direction matches the frozen H1 prediction for all three metrics, but none reaches even a raw p < 0.05 (range 0.086–0.755, non-clustered SEs since only 16 studies), and M1 again performed substantially worse out-of-sample than M0 (ΔRMSE = -0.051). |
| 5 | Air/Water as buffers (low vulnerability) | **NOT SUPPORTED** | H3: Air shows a small, non-significant positive direction (p 0.16–0.73) with a negligible M1 improvement (ΔRMSE = +0.00014); Water shows the OPPOSITE direction on all three metrics with a small M1 degradation (ΔRMSE = -0.00141). No coherent "buffer" signal — direction is not even consistent between Air and Water, the two strata the manuscript groups together. |
| 6 | Variance constraints outperform variance magnitude (the manuscript's title claim) | **NOT SUPPORTED** | This is exactly H2, the primary incremental-value test. `results/ROUND1_PRIMARY_RESULTS.md`: pooled out-of-fold RMSE is *worse* with the constraint metrics added (M0 = 0.16900, M1 = 0.16932, ΔRMSE = -0.00032), only 4/10 folds favor M1, and both negative controls place the observed ΔRMSE well inside the chance distribution (NC1 p = 0.454, NC2 p = 0.583; Holm-adjusted p = 1.000). |
| 7 | D3/1 as an early-warning indicator | **NOT SUPPORTED** | H1-A: standardized coefficient -0.0037 (wrong sign vs. the frozen prediction), raw p = 0.905, Holm-adjusted p = 1.000. |
| 8 | Taylor's Law exponent SHIFT as a warning indicator | **UNTESTED** | Round 1 replicated the static Taylor's Law exponent itself as a DESCRIPTIVE benchmark only (b = 1.930, R² = 0.974 — close to the manuscript's reported b≈1.96, R²≈0.96, `results/round1_descriptive_benchmarks.json`). No time-varying or vulnerability-conditioned "shift" in this exponent was defined or tested anywhere in the frozen protocol — this specific claim was never operationalized. |
| 9 | Year-over-year clustering as a warning indicator | **UNTESTED** | No clustering-based statistic of this kind was defined, frozen, or computed anywhere in `docs/HYPOTHESIS_PROTOCOL.md` or this round's execution. |
| 10 | Conservation prioritization recommendations | **NOT SUPPORTED (as currently grounded)** | These recommendations are premised on claims 3–7, none of which this round supports. This does not mean prioritization by ecological stratum is never warranted on other grounds — only that this project's specific empirical justification for it (constraint-metric-based vulnerability signal) is not supported by this validation. |

## Summary

Of the 10 audited claims: **0 SUPPORTED, 0 WEAKENED, 7 NOT SUPPORTED (2, 3,
4, 5, 6, 7, 10 — not preserved merely by appearing in the manuscript), 1
DESCRIPTIVE ONLY (1), 2 UNTESTED (8, 9).** The manuscript's central title
claim (item 6) is directly and cleanly **NOT SUPPORTED** by the frozen H2
incremental-value test, which per this round's own instruction is the
claim that actually decides it — no individual significant coefficient
would have been sufficient on its own, and none was found significant
after correction in any case.

This audit does not yet rewrite the manuscript. It is the evidentiary
basis a future, separate revision step would use to do so.
