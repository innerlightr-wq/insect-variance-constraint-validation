FROZEN PROTOCOL COMMIT: 21e6992

# Round 1 negative controls

## NC1_within_study_constraint_permutation

- n_permutations: 2000
- observed_delta_rmse: -0.00032198907393388154
- null_mean: -0.00041216507101177007
- null_sd: 0.0005010840402212633
- null_q95: 0.0003363091337331536
- empirical_one_sided_p: 0.4542728635682159
- expected_under_true_null: delta_rmse collapses toward the null distribution above

## NC2_within_study_outcome_permutation

- n_permutations: 2000
- observed_delta_rmse: -0.00032198907393388154
- null_mean: -0.0002415581644166916
- null_sd: 0.00044405431789810296
- null_q95: 0.0004716931470730892
- empirical_one_sided_p: 0.5827086456771614
- expected_under_true_null: delta_rmse collapses toward the null distribution above

## NC3_time_reversal_diagnostic

- n: 1126
- reversed_M0_rmse: 0.16198260938716139
- reversed_M1_rmse: 0.1691406538503614
- reversed_delta_rmse: -0.007158044463200008
- interpretation: diagnostic only, not evidence for or against H1/H2 in either direction. A large positive reversed_delta_rmse here would flag a leaked time-invariant confound in the pipeline; it does not, per the frozen protocol, count toward or against the primary verdict.

