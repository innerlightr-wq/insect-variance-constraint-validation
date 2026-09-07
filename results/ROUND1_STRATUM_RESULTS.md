FROZEN PROTOCOL COMMIT: 21e6992

# Round 1 H3 stratum results (SECONDARY)

Only strata passing the frozen Task 14 adequacy gate are tested (Air, Water, Herb layer, Soil surface). Trees and Underground are excluded, not tested. H3 is secondary regardless of outcome and is never promoted to the primary conclusion.

## Air
- n series: 406, n studies: 40, CV folds used: 5
- M0 RMSE 0.15766, M1 RMSE 0.15752, delta 0.00014
  - D31: coef=0.0371, raw p=0.2170, cluster-robust SE used=True, direction matches H1=True
  - D41: coef=0.0385, raw p=0.1571, cluster-robust SE used=True, direction matches H1=True
  - Q9050: coef=0.0035, raw p=0.7337, cluster-robust SE used=True, direction matches H1=True

## Water
- n series: 326, n studies: 30, CV folds used: 5
- M0 RMSE 0.19989, M1 RMSE 0.20130, delta -0.00141
  - D31: coef=-0.0359, raw p=0.5361, cluster-robust SE used=True, direction matches H1=False
  - D41: coef=-0.0422, raw p=0.4346, cluster-robust SE used=True, direction matches H1=False
  - Q9050: coef=-0.0080, raw p=0.5631, cluster-robust SE used=True, direction matches H1=False

## Herb layer
- n series: 198, n studies: 10, CV folds used: 5
- M0 RMSE 0.25705, M1 RMSE 0.29791, delta -0.04086
  - D31: coef=-0.0686, raw p=0.0922, cluster-robust SE used=False, direction matches H1=False
  - D41: coef=-0.0752, raw p=0.0571, cluster-robust SE used=False, direction matches H1=False
  - Q9050: coef=-0.0223, raw p=0.0830, cluster-robust SE used=False, direction matches H1=False

## Soil surface
- n series: 136, n studies: 16, CV folds used: 5
- M0 RMSE 0.22752, M1 RMSE 0.27825, delta -0.05074
  - D31: coef=0.1251, raw p=0.0890, cluster-robust SE used=False, direction matches H1=True
  - D41: coef=0.1186, raw p=0.0857, cluster-robust SE used=False, direction matches H1=True
  - Q9050: coef=0.0068, raw p=0.7553, cluster-robust SE used=False, direction matches H1=True

## Direction consistency across strata (per metric)
- D31: {'Air': 1, 'Water': -1, 'Herb layer': -1, 'Soil surface': 1} -> all same sign: False
- D41: {'Air': 1, 'Water': -1, 'Herb layer': -1, 'Soil surface': 1} -> all same sign: False
- Q9050: {'Air': 1, 'Water': -1, 'Herb layer': -1, 'Soil surface': 1} -> all same sign: False
