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
| BL-18 | Pairwise `CandidatePair` model: fix `row_indices` to always length 2 (explode key-collision clusters pairwise; drop NN union-find clustering); relabel `ParamSpec.label` for Levenshtein/NCD (`"Radius"`) and N-Gram (`"N-Gram size"`) | M4 | Must | Planned |
| BL-19 | Merge `routers/algorithm.py` + `routers/results.py` into one combined `GET/POST /algorithm` page (Method -> Distance function -> parameter field, filtered/shown per `frd.md` FR-3.2/FR-3.3); `GET /results` becomes a redirect to `/algorithm` | M4 | Must | Planned |
| BL-20 | Real `ComputeBackend.replace_values` implementation | M4 | Must | Planned |
| BL-21 | `merge_service.apply_merge` — pairwise rewrite of both rows per checked pair, conflict detection/blocking (FR-6.3), append version + rerun matching only on a successful merge, no-op on zero-checked (FR-6.5) | M4 | Must | Planned |
| BL-22 | Live HTMX results table: `app/static/js/match.js` (client-side checkbox-default + click-to-set-value interactions, FR-5.4/FR-5.5), `POST /merge` endpoint, editable "New cell value" input + "Merge?" checkbox + "Merge selected & re-cluster" button in `_pair_row.html`/`_results_table.html` | M4 | Must | Planned |
| BL-23 | `csv_service.build_export` + `GET /export.csv` | M5 | Must | Planned |
| BL-24 | GitHub Actions CI workflow (ruff check/format, pytest, matrix 3.11/3.12) | M5 | Must | Planned |
| BL-25 | Full-stack smoke test (upload->mapping->algorithm->check "Merge?"->merge->export; updated from the pre-M4 plan's "accept" step, which no longer exists) | M5 | Must | Planned |
| BL-26 | `docs/design/ui-design-spec.md` — OpenRefine-derived palette/typography/spacing/component spec | chore-frontend-redesign | Must | Done |
| BL-27 | Restructure `app/static/css/styles.css` into design-token-based system (palette, spacing, table/button states) per ui-design-spec | chore-frontend-redesign | Must | Planned |
| BL-28 | Restyle `base.html` header banner + `mapping.html`/`algorithm.html` control-row/control-group layout | chore-frontend-redesign | Must | Planned |
| BL-29 | Restyle `results.html`/`_results_table.html`/`_pair_row.html` (table zebra/hover, disabled-button treatment) — `results.html` itself is later merged into `algorithm.html` by M4 (BL-19); the `_results_table.html`/`_pair_row.html` component styling this item produces carries forward unchanged | chore-frontend-redesign | Must | Planned |
| BL-30 | Extend `.claude/agents/tester.md` with Playwright Visual QA pass; add `playwright` to `requirements-dev.txt` | chore-frontend-redesign | Must | Done |

## Priority legend

- **Must**: required for the milestone to be considered complete per the plan/issue.
- **Should**: important but could slip to a follow-up pass without blocking the milestone's core value.
- **Could**: nice-to-have, not currently committed to any milestone.

## Status legend

- **Done**: shipped and verified (tests passing, reviewer pass complete).
- **In Progress**: BA pass complete; coder/tester/reviewer passes in progress.
- **Planned**: scoped for an upcoming milestone, not yet built.
- **Open question**: scoping ambiguity needs resolution before/while building (see the milestone's acceptance-criteria file for detail).
