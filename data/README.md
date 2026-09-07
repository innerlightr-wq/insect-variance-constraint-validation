# Data directory

**No raw dataset content is committed to this repository.** Everything
under `data/raw/` and `data/processed/` is `.gitignore`d and must be
rebuilt locally. See `docs/DATA_PROVENANCE.md` for full provenance,
licensing (CC BY 4.0 — redistribution is permitted, but this repository
does not commit raw third-party data as a matter of hygiene/convention),
and checksums.

## Rebuilding `data/raw/insect_knb/`

```bash
mkdir -p data/raw/insect_knb && cd data/raw/insect_knb

curl -sS "https://knb.ecoinformatics.org/knb/d1/mn/v2/object/doi:10.5063%2FF11V5C9V" \
  -o A_global_database_of_long_term_changes_in_insect.xml

curl -sS "https://knb.ecoinformatics.org/knb/d1/mn/v2/object/urn%3Auuid%3A82b3f580-abd2-4bb3-b0be-a9e2a34136eb" \
  -o DataSources.csv

curl -sS "https://knb.ecoinformatics.org/knb/d1/mn/v2/object/urn%3Auuid%3A2fc48341-36e5-4b87-b75f-654eebe643f0" \
  -o PlotData.csv

curl -sS "https://knb.ecoinformatics.org/knb/d1/mn/v2/object/urn%3Auuid%3A71cf3825-91e1-4ca9-8457-b5eefb1514c4" \
  -o SampleData.csv

curl -sS "https://knb.ecoinformatics.org/knb/d1/mn/v2/object/urn%3Auuid%3Ad5fbebb4-855c-4724-8146-94f8df497480" \
  -o InsectAbundanceBiomassData.csv
```

Then verify integrity against `data/provenance.json`:

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from insect_variance_protocol import verify_checksum
import json
prov = json.load(open('data/provenance.json'))
for f in prov['files']:
    if 'md5_reported_by_dataone' not in f: continue
    path = f'data/raw/insect_knb/{f[\"entity_name\"]}'
    ok = verify_checksum(path, f['md5_reported_by_dataone'])
    print(path, 'OK' if ok else 'MISMATCH')
"
```

`InsectAbundanceBiomassData.csv` (and only that file, of the four CSVs) is
**not valid UTF-8** — read it with `encoding="latin-1"` (confirmed
necessary and used throughout `src/`).

## Layout

- `data/raw/insect_knb/` — the four CSVs plus the EML metadata document,
  exactly as downloaded, never modified.
- `data/processed/` — reserved for derived tables (e.g. the eligible-series
  table) built by `src/` scripts; also gitignored. Nothing has been
  written here yet in Round 0 — eligibility/adequacy tables are computed
  in-memory and only their aggregate counts are written to `results/`.
