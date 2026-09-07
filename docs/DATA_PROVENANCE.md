# Data provenance — primary dataset

**No raw dataset content is reproduced in this file.** Everything below is
metadata: URLs, identifiers, checksums, sizes, and counts, gathered by
directly querying the DataONE/KNB APIs in this session (not assumed from
the manuscript). Machine-readable version: `data/provenance.json`.

## Identification

- **Exact dataset title (verified from the EML metadata document, not the
  manuscript):** "A global database of long-term changes in insect
  assemblages"
- **DOI:** `10.5063/F11V5C9V` — https://doi.org/10.5063/F11V5C9V
- **Repository/provider:** Knowledge Network for Biocomplexity (KNB), a
  DataONE member node
- **Citation** (from the EML metadata's own creator list, 20 authors):
  van Klink, R., D.E. Bowler, J.M. Chase, O. Comay, M.M. Driessen,
  S.K.M. Ernest, A. Gentile, F. Gilbert, K. Gongalsky, J. Owen, G. Pe'er,
  I. Pe'er, V.H. Resh, I. Rochlin, S. Schuch, A.E. Swengel, S.R. Swengel,
  T.L. Valone, R. Vermeulen, and T. Wepprich. 2020. *A global database of
  long-term changes in insect assemblages.* Knowledge Network for
  Biocomplexity.
- **Publication year (EML `<pubDate>`):** 2020

## License / redistribution

The EML metadata's `<intellectualRights>` element states directly:

> "This work is licensed under the Creative Commons Attribution 4.0
> International License. To view a copy of this license, visit
> http://creativecommons.org/licenses/by/4.0/."

**Redistribution is permitted** (CC BY 4.0, attribution required). This
repository nonetheless does **not** commit the raw data — the same
repo-hygiene convention used in the `linear-a-constraint-validation`
project — and instead commits this provenance record, checksums, and
download instructions (see `data/README.md`).

## Version finding — disclosed, not silently resolved

Querying the DataONE system metadata for the exact DOI-pinned PID
(`doi:10.5063/F11V5C9V`) shows `archived: false` (still resolvable) but
**`obsoletedBy: urn:uuid:e2501439-4af9-438f-8bae-abeef1459727`** — a newer
revision exists in the KNB system that never received its own separate
DOI. **This repository uses the exact object the manuscript's DOI
resolves to** (uploaded 2020-04-08T15:43:46Z, sysmeta last modified
2020-10-01T14:15:11Z), matching what any reader following the citation
would retrieve, not the newer unversioned revision. This is a disclosed
methodological choice, not an oversight.

## How the files were located (method, for reproducibility)

1. Resolved the DOI via DataONE's coordinating-node resolve API
   (`https://cn.dataone.org/cn/v2/resolve/doi%3A10.5063%2FF11V5C9V`),
   confirming the PID exists on both the DataONE CN and the KNB member
   node.
2. Fetched that PID's EML metadata document directly
   (`https://knb.ecoinformatics.org/knb/d1/mn/v2/object/doi:10.5063%2FF11V5C9V`)
   and confirmed the dataset title and entity (file) names from it — not
   from the manuscript.
3. Queried the DataONE Solr search index
   (`.../v2/query/solr/?q=identifier:"doi:10.5063/F11V5C9V"`) for the
   `documents` field, which lists the individual data-object PIDs
   belonging to this metadata record's resource map.
4. Fetched system metadata (`.../v2/meta/<pid>`) for each of the 7 object
   PIDs to get each file's real name, format, size, and MD5 checksum.
5. Downloaded the 4 CSV data files plus the EML XML itself via the
   `.../v2/object/<pid>` endpoint, and independently recomputed MD5 (to
   verify against DataONE's own reported checksum) and SHA-256 (for this
   project's own provenance record) locally.

## Downloaded files

| entity | DataONE PID | size (bytes) | MD5 (DataONE, verified match) | SHA-256 (computed locally) |
|---|---|---:|---|---|
| DataSources.csv | `urn:uuid:82b3f580-...` | 30,660 | `8106974fee871582f7333b27e2e2d6a3` | `222ba063a565d46a6c8707e2e4816505bd9db7cb401e3795cd727c8cb1d740f2` |
| PlotData.csv | `urn:uuid:2fc48341-...` | 818,940 | `2513a3b0fce879eef2f2a228dde88ea1` | `e8ef5812ebfa7df233feb62fbaf5009710dd5af6938f47414733e74b1887a915` |
| SampleData.csv | `urn:uuid:71cf3825-...` | 35,862 | `85bd098a7c8dc388d6e856f325c33ad1` | `71fd709d9df4b2cffa161ce74084cb3c80a2181528445de688880993f33ba882` |
| InsectAbundanceBiomassData.csv | `urn:uuid:d5fbebb4-...` | 3,336,200 | `b55a4cfe14e0dd5b2508b24e59c57bf2` | `cf86388e9905d25fed8f8d6fb188280f1f4ba272cd3e3441c2610d6339fb5da0` |
| A_global_database_of_long_term_changes_in_insect.xml (EML metadata) | `doi:10.5063/F11V5C9V` | 88,855 | (SHA-1 reported by DataONE: `8b8367b81bb92c1d5cb02baee2eaef8eb7f3f347`) | `998a64f72119c636013ca00b9fd1e9c2d49e796a709de7b44481f31dc5320a5c` |

**All four CSV MD5 checksums matched DataONE's own reported sysmeta
exactly** — integrity of the download is directly verified, not assumed.

Full paths: `data/raw/insect_knb/<entity_name>` (gitignored; see
`data/README.md` for the exact download commands to reproduce this).

**Download date:** 2026-09-07 (this session).

## Not downloaded (disclosed, with reason)

- `References_to_original_data_sources.pdf` — citation list, not needed for
  schema/eligibility/protocol work this round.
- `ReadMe.docx` — prose documentation; the EML metadata plus direct CSV
  inspection were sufficient.
- `Google_Earth_locations_of_all_datasets.kml` — geographic visualization
  aid, not needed this round.

## Independent verification of the manuscript's scale claims

The manuscript states approximately 70,955 observations and ~1,663 plots.
**These were independently verified from the downloaded files, not
assumed:**

- `InsectAbundanceBiomassData.csv` has exactly **70,955** data rows.
- `Plot_ID` has exactly **1,663** unique values within
  `InsectAbundanceBiomassData.csv`, and every one of them is found in
  `PlotData.csv` with zero referential-integrity mismatches (see
  `results/DATA_ADEQUACY_AUDIT.md`).

Both headline claims check out exactly against the real files. This does
**not** mean every manuscript claim is assumed correct going forward —
each specific claim used later (e.g. the Taylor's Law exponent, the
CV-of-CVs figure) is independently re-derived from these same raw files
in its own document, never cited from the manuscript as ground truth.
