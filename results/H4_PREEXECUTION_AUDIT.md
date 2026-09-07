H4 FROZEN PROTOCOL COMMIT: 3e30670
PARENT FEASIBILITY COMMIT: d3246d9

# H4 pre-execution integrity audit

- commits exist: {'round0': True, 'round1': True, 'round2a': True, 'h4_freeze': True}
- HEAD: 3e30670b1a1a50510338c96bbb131b54e89681c4
- H4 protocol files match freeze commit 3e30670 (zero diff): True
- tests: 106 passed in 47.89s (expected 106 passed): True

## Frozen H4 choices (machine-readable summary, protocols/h4_protocol.json)

- minimum constituent series: 15
- historical window: 10 years -- fixed 10-year history window (study's own first 10 union-years) then a fully held-out later period (all remaining union-years); non-overlapping, deterministic, no window search
- predictor: SD_i(CV_i) / Mean_i(CV_i)
- outcome: OLS slope of log1p(Number) on Year over a constituent series' own Round-1 late window
- outcome eligibility filter: series.late_year_min > max(study.hist_years) -- i.e. that series' Round-1 late window must fall entirely after the study's H4 historical cutoff
- predicted direction: positive
- M0: ['baseline_mean_log1p', 'baseline_cv', 'baseline_trend', 'baseline_n', 'baseline_span']
- M1: ['baseline_mean_log1p', 'baseline_cv', 'baseline_trend', 'baseline_n', 'baseline_span', 'C_g']
- primary statistic: RMSE(M0) - RMSE(M1), pooled out-of-fold across LOSO folds
- permutation count: 10000, seed: 20260907
- alpha: 0.05
- support rule: {
  "SUPPORTED": "delta_rmse > 0 AND primary permutation p <= 0.05 (one-sided)",
  "NOT_SUPPORTED": "primary permutation p > 0.05, regardless of delta_rmse sign; OR delta_rmse <= 0 regardless of p",
  "DIRECTIONALLY_OPPOSITE": "primary permutation test rejects the null against the predicted direction (delta_rmse reliably negative)",
  "UNINTERPRETABLE_BLOCKED": "fewer than 10 H4-eligible studies survive every gate"
}

## READY_FOR_H4_EXECUTION: **True**
