# Round 1 pre-execution integrity audit

FROZEN PROTOCOL COMMIT: 21e6992

## 1. Git state
- working tree was confirmed clean, and HEAD confirmed at the frozen commit, manually and separately, BEFORE any Round 1 file was written (Task 1 step 1-2).
- working tree clean at the time this script itself ran: False (expected false — this script and its own output are themselves new Round 1 files; not part of the readiness gate, see note in JSON)
- HEAD: 21e699228f40bf4585e42d5896a7835de0b21dca
- HEAD matches frozen commit (no unauthorized commits on top of the freeze): True

## 2. Checksums (data/provenance.json vs. local files)
- all files verified: True
  - DataSources.csv: OK
  - PlotData.csv: OK
  - SampleData.csv: OK
  - InsectAbundanceBiomassData.csv: OK

## 3. Eligible population
- eligible series: 1129 (frozen: 1129) -> match: True
- eligible studies: 99 (frozen: 99) -> match: True

## 4. Grouped fold reproduction (10-fold GroupKFold on DataSource_ID)
- no study split across train/test in any fold: True
- every eligible series in exactly one test fold: True
- fold test sizes: [151, 132, 106, 106, 106, 106, 106, 106, 105, 105]
- minimum test fold size: 105 (>= 20 required): True
- fallback required: False
- fallback invoked: False

## READY TO EXECUTE ROUND 1: **True**
