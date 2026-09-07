# CV-of-CVs chronological separation design feasibility (ROUND 2A, Task 10)

Structural only -- no outcome value is read. Historical-portion adequacy uses the same >=5-series / >=2-observations-per-series criteria as Task 8.

## A_50_50
- studies retained: 38
- median future years available: 9.5
- leakage risk: none by construction -- split is by unique-year rank, mirroring insect_variance_protocol.chronological_split's own assertion pattern; historical portion never reads a future-portion year.

## B_60_40
- studies retained: 38
- median future years available: 8.0
- leakage risk: none by construction -- split is by unique-year rank, mirroring insect_variance_protocol.chronological_split's own assertion pattern; historical portion never reads a future-portion year.

## C_fixed_10yr_history_plus_heldout_later
- studies retained: 35
- median future years available: 10.0
- leakage risk: none by construction, same rationale as designs A/B.

