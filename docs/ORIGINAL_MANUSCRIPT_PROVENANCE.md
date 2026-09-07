# Original manuscript provenance

**The original manuscript is preserved unmodified. It was not moved, renamed, or overwritten.**

## Location and identification

Three byte-identical copies were found in `~/Downloads` (typical repeated-download naming from a browser):

| path | size | modified | SHA-256 |
|---|---:|---|---|
| `~/Downloads/EcologicalEntomology.pdf` (canonical, earliest) | 379,944 bytes | 2026-05-03 10:53:04 | `be3327410a6b2ef8c1e1d16bc39bffe7b2a92465b5fd3ae91431260c77cd0186` |
| `~/Downloads/EcologicalEntomology (1).pdf` | 379,944 bytes | 2026-05-03 10:58 | (identical SHA-256) |
| `~/Downloads/EcologicalEntomology (1) (1).pdf` | 379,944 bytes | 2026-09-07 10:57 (later filesystem copy, same content) | (identical SHA-256) |

All three are byte-for-byte identical (verified by SHA-256). **The canonical original referenced throughout this revision is `~/Downloads/EcologicalEntomology.pdf`** (earliest timestamp, no duplicate suffix).

- **Format:** PDF (compiled; no `.tex` source was found alongside it in `~/Downloads`)
- **Title (from document text):** "Variance Constraints, Not Variance Magnitude, as Indicators of Insect Community Vulnerability: Evidence from Long-Term Insect Abundance Monitoring"
- **Author:** Elias De Jesús, Independent Researcher, ORCID 0009-0007-0190-9143 (matches this project's own author record)
- **Length:** 22 pages

## Identification method

Located via:
1. Filename search across `~/Downloads` for insect/variance/constraint/vulnerability terms — no hits by filename.
2. Spotlight (`mdfind`) content search for the exact title phrase and "insect community vulnerability" — surfaced `EcologicalEntomology.pdf` and its two duplicates as the only matches.
3. Confirmed by reading the document: title, author, ORCID, and content (CV-of-CVs, D3/1, Taylor's Law, six ecological strata, bioacoustic/paleontological sections) all match the manuscript this validation program was designed to test.

## Because the source is PDF, not TeX

No original `.tex` source was found. Per instruction, the revised manuscript is authored fresh as a new TeX file (`manuscript/insect_variance_constraint_validation_revised.tex`) rather than attempting to reverse-engineer or edit the original PDF's typesetting. The original PDF's full content (all 22 pages: abstract, introduction, methods, results, interpretation, monitoring/conservation implications, epistemic status, limitations, conclusion, data availability, author contributions, references) was read in full and used only as the source of original claims to be classified and revised — never modified, never overwritten, and not committed to this repository (see Data/third-party-content policy below).

## Third-party content policy

The original manuscript is **not** copied into this repository's tracked files. It remains only at its original location in `~/Downloads`, per this project's existing convention of not redistributing third-party or pre-existing content without a separate, deliberate licensing decision (mirroring how raw corpus data is handled — see `data/README.md`). This provenance document records its identity and checksum so the revision's basis is verifiable without redistributing the file itself.
