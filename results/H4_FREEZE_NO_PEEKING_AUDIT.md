# H4 freeze no-peeking audit (Task 20)

AST-verified: `src/h4_pipeline.py` and `tests/test_h4_pipeline.py` never load the real corpus (no `read_csv`/`read_json`/`read_excel` call, no reference to `data/raw/insect_knb`, `InsectAbundanceBiomassData.csv`, or a `DATA_DIR` constant anywhere in either file). Every H4 pipeline function takes already-built DataFrames as arguments (dependency injection); every test uses inline synthetic fixtures.

This structurally guarantees, not merely asserts by prose, that this freeze round could not have computed:
- no real-data predictor-outcome correlation computed
- no H4 regression coefficient computed against real data
- no H4 RMSE difference computed against real data
- no H4 R^2 computed against real data
- no H4 p-value computed against real data
- no permutation result computed against real data
- no subgroup effect computed against real data

- `src/h4_pipeline.py`: CLEAN
- `tests/test_h4_pipeline.py`: CLEAN

## H4_NO_PEEKING_CONFIRMED: **True**
