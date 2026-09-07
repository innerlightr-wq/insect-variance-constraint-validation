# Final manuscript claim crosswalk

Built from the original manuscript (`docs/ORIGINAL_MANUSCRIPT_PROVENANCE.md`) against the complete, authoritative validation record (commits `21e6992`, `206742f`, `d3246d9`, `3e30670`, `8d6db88`). Written **before** any prose in the revised manuscript, per instruction. No claim is preserved merely because it appeared in the original.

| # | Original claim | Final status | Evidence / commit | Revision action |
|---|---|---|---|---|
| 1 | `CV_CVs ≈ 0.610` | **REPLACED BY VALIDATED RESULT** | `docs/CV_OF_CV_INTERPRETATION.md`, `21e6992` (independently recomputed: 0.512) | Report 0.512 as this project's own validated recomputation; disclose it is in the same general range as, but not an exact reproduction of, the original 0.610 (different population/aggregation choices, `docs/CV_OF_CV_INTERPRETATION.md`). Never present 0.610 as this project's own result. |
| 2 | CV-of-CVs represents a universal ecological constant/bound | **NOT SUPPORTED** | `docs/CV_OF_CV_INTERPRETATION.md` (`21e6992`); `docs/H4_CLAIM_STATUS.md` (`8d6db88`) | Remove "universal constant"/"bound" framing entirely; replace with the explicit finite-dispersion-≠-ecological-bound distinction. |
| 3 | CV-of-CVs represents contextual empirical structure | **SUPPORTED** | `docs/H4_CLAIM_STATUS.md` item 1 (`8d6db88`): `C_g` computed for 16 study-windows (11 usable), real, defined, non-degenerate values | Retain, reframed explicitly as *contextual*, never universal — this is the one claim H4 affirmatively demonstrates. |
| 4 | CV-of-CVs is an early-warning indicator | **NOT SUPPORTED** | H4 primary result, `8d6db88`: ΔRMSE = −0.002354, permutation p = 0.5304 | Remove as an established claim; may be discussed only as a *tested and rejected* prospective hypothesis. |
| 5 | `D3/1` predicts vulnerability | **NOT SUPPORTED** | Round 1 H1-A, `206742f`: wrong direction, raw p=0.905, Holm p=1.000 | Remove predictive framing; report the null result plainly. |
| 6 | `D4/1` predicts vulnerability | **NOT SUPPORTED** | Round 1 H1-B, `206742f`: wrong direction, raw p=0.871, Holm p=1.000 | Same as #5. |
| 7 | `Q90/50` predicts vulnerability | **NOT SUPPORTED** | Round 1 H1-C, `206742f`: wrong direction, raw p=0.043, Holm p=0.171 | Same as #5. Explicitly note raw p=0.043 must **not** be reported as "near-significant" — direction was wrong and Holm correction fails it. |
| 8 | Constraint metrics outperform conventional variance information (title claim) | **NOT SUPPORTED** | Round 1 H2, `206742f`: ΔRMSE=−0.00032, 4/10 folds, Holm p=1.000; NC1 p=0.454, NC2 p=0.583 | This is the manuscript's central claim and its title. Title must change (Task 4); central message inverted to the negative result. |
| 9 | Herb layer is a vulnerability bottleneck | **NOT SUPPORTED** | Round 1 H3 (secondary), `206742f`: ΔRMSE=−0.041, direction opposite frozen H1 prediction | Remove "bottleneck" language; report as a tested, non-significant, secondary stratum result where M1 performed *worse*. |
| 10 | Soil surface is a vulnerability bottleneck | **NOT SUPPORTED** | Round 1 H3 (secondary), `206742f`: ΔRMSE=−0.051, raw p 0.086–0.755 (uncorrected, non-clustered SEs, 16 studies) | Same as #9. |
| 11 | Air is a buffer | **NOT SUPPORTED** | Round 1 H3 (secondary), `206742f`: ΔRMSE=+0.00014 (negligible), p 0.16–0.73 | Remove "buffer" language; report as a negligible, non-significant secondary effect. |
| 12 | Water is a buffer | **NOT SUPPORTED** | Round 1 H3 (secondary), `206742f`: ΔRMSE=−0.00141, direction opposite frozen prediction | Same as #11 — note direction is not even consistent with Air, undermining the shared "buffer" framing. |
| 13 | Taylor's Law scaling (`b≈1.96`, `R²≈0.96`) | **DESCRIPTIVE ONLY** | Round 1 descriptive benchmark, `206742f`: b=1.930, R²=0.974 | Retain as a successful descriptive replication; explicitly labeled not evidence for H1/H2/H4 anywhere it is reported. |
| 14 | Taylor exponent shift is an early-warning indicator | **UNTESTED** | `docs/MANUSCRIPT_CLAIM_AUDIT.md` item 8 (`206742f`) — only the static exponent was ever replicated; no time-varying "shift" statistic was defined or computed | Remove as a claim; may be named only as an untested, unoperationalized idea for future work. |
| 15 | Year-over-year transition-ratio clustering is an early-warning indicator | **UNTESTED** | `docs/MANUSCRIPT_CLAIM_AUDIT.md` item 9 (`206742f`) — no such statistic was ever defined in the frozen protocol | Same as #14. |
| 16 | Bioacoustic classification data validate the mechanism | **UNTESTED** | `docs/SCOPE_AND_FUTURE_WORK.md` (`21e6992`) — explicitly out of scope for the entire validation program, never touched by any round | Remove from Results/Discussion entirely; retain only as a labeled future-monitoring application in Future Work, never as evidence. |
| 17 | Paleontological (chondrichthyan) cross-scale generalization | **UNTESTED** | `docs/SCOPE_AND_FUTURE_WORK.md` (`21e6992`) — explicitly out of scope, never touched | Remove from Results/Discussion entirely; retain only as a labeled, untested cross-scale analogy in Future Work, never implying confirmation. |
| 18 | Conservation-prioritization recommendations (prioritize Herb/Soil/Underground) | **NOT SUPPORTED (as grounded)** | Follows directly from #8–10 (`206742f`) and H4 (`8d6db88`), both NOT SUPPORTED | Remove specific prioritization recommendations; replace with an explicit caution against using these metrics for conservation prioritization absent independent prospective validation. |
| 19 | Causal constraint-transmission mechanism ("coupling bottlenecks," "perturbations propagate") | **UNTESTED** | No causal design exists anywhere in `21e6992`–`8d6db88`; the original manuscript itself already disclaimed causal inference in its own Epistemic Status section | Remove causal-sounding language ("propagate," "transmit," "amplify") describing a mechanism that was never tested; the original manuscript's own disclaimer is honored, not weakened, by removing the language that exceeded it. |

## Numbers explicitly superseded (never reused from the original)

| original manuscript value | validated replacement | source |
|---|---|---|
| `CV_CVs = 0.610` | `0.512` | `docs/CV_OF_CV_INTERPRETATION.md` (`21e6992`) |
| Taylor `b = 1.959`, `R² = 0.962` | `b = 1.930`, `R² = 0.974` | Round 1 descriptive benchmark (`206742f`) |
| 70,955 observations / 1,663 plots / 1925–2018 | **unchanged, independently reconfirmed** | `docs/DATA_PROVENANCE.md` (`21e6992`) |
