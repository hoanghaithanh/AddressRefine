# Product Backlog — AddressRefine

Status: Living document, added to on every BA pass. IDs are stable once
assigned; do not renumber on later edits.

| ID | Title | Milestone | Priority | Status |
|---|---|---|---|---|
| BL-1 | Project scaffold: FastAPI app factory, settings, session store, cookie middleware | M1 | Must | Done |
| BL-2 | CSV upload with 10MB streaming size limit and empty/unparseable-CSV rejection | M1 | Must | Done |
| BL-3 | `ComputeBackend` ABC + `PandasComputeBackend` (load/headers/extract/to_csv; `replace_values` stubbed) | M1 | Must | Done |
| BL-4 | Column mapping form with best-guess pre-fill and full per-column header validation | M1 | Must | Done |
| BL-5 | `MatchingAlgorithm` ABC, `ParamSpec`, `AlgorithmOutput`, `AlgorithmFamily` (`app/algorithms/base.py`) | M2 | Must | Done |
| BL-6 | Algorithm registry (`app/algorithms/registry.py`) | M2 | Must | Done |
| BL-7 | `FingerprintAlgorithm` (key-collision, no params) | M2 | Must | Done |
| BL-8 | `NGramFingerprintAlgorithm` (key-collision, param `n`, default 2) | M2 | Must | Done |
| BL-9 | `matching_service.run_matching` — key-collision orchestration path | M2 | Must | Done |
| BL-10 | `GET/POST /algorithm` router + template | M2 | Must | Done |
| BL-11 | `GET /results` router + template (read-only; accept/reject inert) | M2 | Must | Done |
| BL-12 | Resolve mapping->algorithm redirect target (OQ-M2-1) | M2 | Should | Done |
| BL-13 | `compute_blocks(rows: dict[int, dict[str, str]])` (zip-prefix / city fallback / shared-bucket blocking; no `ColumnMapping` arg) | M3 | Must | In Progress |
| BL-14 | `normalized_compression_distance` (NCD, bz2-based, order-averaged; empty+empty → 0.0) | M3 | Must | In Progress |
| BL-15 | `LevenshteinNNAlgorithm` (rapidfuzz + `score_cutoff`; param `threshold` non-neg int, default 3) | M3 | Must | In Progress |
| BL-16 | `NCDAlgorithm` (PPM-approx; UI threshold int 1–10, default 3; internal scaling /10) | M3 | Must | In Progress |
| BL-17 | Extend `matching_service` with NN path: `extract_columns` → `compute_blocks` → algorithm → union-find → `CandidatePair` with `pair_id` + max-distance | M3 | Must | In Progress |
| BL-17a | Add `pair_id: str` field to `CandidatePair` in `domain.py` (uuid4, assigned by `matching_service`) | M3 | Must | In Progress |
| BL-17b | Extend `POST /algorithm` router to validate `threshold` for Levenshtein (≥ 0) and NCD (1–10); extend `algorithm.html` with `threshold` input | M3 | Must | In Progress |
| BL-17c | Extend `results.html` with per-algorithm distance scale sub-label ("edit distance" / "NCD score (0–1)") | M3 | Must | In Progress |
| BL-18 | `CandidatePair` full model (status, representative fields) | M4 | Must | Planned |
| BL-19 | Results router mutation endpoints (accept/reject/representative) | M4 | Must | Planned |
| BL-20 | Real `ComputeBackend.replace_values` implementation | M4 | Must | Planned |
| BL-21 | `merge_service.apply_merge` (rewrite rows, append version, rerun matching) | M4 | Must | Planned |
| BL-22 | `POST /merge` router + live `_pair_row.html` | M4 | Must | Planned |
| BL-23 | `csv_service.build_export` + `GET /export.csv` | M5 | Must | Planned |
| BL-24 | GitHub Actions CI workflow (ruff check/format, pytest, matrix 3.11/3.12) | M5 | Must | Planned |
| BL-25 | Full-stack smoke test (upload->mapping->algorithm->accept->merge->export) | M5 | Must | Planned |

## Priority legend

- **Must**: required for the milestone to be considered complete per the plan/issue.
- **Should**: important but could slip to a follow-up pass without blocking the milestone's core value.
- **Could**: nice-to-have, not currently committed to any milestone.

## Status legend

- **Done**: shipped and verified (tests passing, reviewer pass complete).
- **In Progress**: BA pass complete; coder/tester/reviewer passes in progress.
- **Planned**: scoped for an upcoming milestone, not yet built.
- **Open question**: scoping ambiguity needs resolution before/while building (see the milestone's acceptance-criteria file for detail).
