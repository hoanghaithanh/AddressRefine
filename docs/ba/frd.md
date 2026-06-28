# Functional Requirements Document — AddressRefine

Status: Living document. Last revised: M2 BA pass (2026-06-28). Reflects
functionality shipped through M1 plus functionality planned for M2; later
milestones (M3-M5) are described at the level of detail available in the
plan and will be filled in/corrected as each ships.

Each functional requirement (FR) is referenced from `traceability-matrix.md`
and from the relevant milestone's acceptance-criteria file.

## FR-1 — CSV Upload (shipped, M1)

- **FR-1.1**: The system shall accept a single CSV file upload via
  `POST /upload` (multipart form, field name `file`).
- **FR-1.2**: The system shall reject uploads exceeding 10 MB
  (`Settings.MAX_UPLOAD_BYTES`), detected by streaming/chunked size
  accounting (1 MB chunks) rather than buffering the whole file first, and
  shall respond with HTTP 400 and a flash error message.
- **FR-1.3**: The system shall reject CSVs that parse to zero data rows or
  zero columns (HTTP 400, flash error), via
  `PandasComputeBackend.load_csv` raising `ValueError`.
- **FR-1.4**: CSV parsing shall use `dtype=str, keep_default_na=False` so
  leading zeros in zip-like fields and literal `"NA"` tokens are preserved
  verbatim rather than coerced to numeric/NaN.
- **FR-1.5**: On successful upload, the system shall start a new
  `DatasetVersion` (`version=1`, `created_from_merge=False`) as the
  session's sole version, clear any prior `session.mapping`, and redirect
  to `/mapping` (HTTP 303).

## FR-2 — Column Mapping (shipped, M1)

- **FR-2.1**: The system shall render a mapping form (`GET /mapping`)
  listing the uploaded CSV's headers as options for four logical fields:
  street (required), zip, city, country (all optional, but at least one of
  zip/city required).
- **FR-2.2**: If no mapping has been confirmed yet, the system shall
  pre-select a best-guess mapping based on case-insensitive substring match
  on header names (`"street"`/`"address"` -> street; `"zip"` -> zip;
  `"city"` -> city; `"country"` -> country).
- **FR-2.3**: If a mapping was already confirmed in this session, the GET
  form shall reflect that saved mapping rather than recomputing the
  best-guess (so navigating back doesn't clobber a deliberate user choice).
- **FR-2.4**: On `POST /mapping`, the system shall validate via
  `MappingForm` (pydantic) that `street_col` is non-empty and at least one
  of `zip_col`/`city_col` is supplied; validation failure re-renders the
  form with HTTP 422 and a flash error.
- **FR-2.5**: Every non-empty submitted column name (street, zip, city,
  country) shall be checked against the real CSV headers obtained via
  `ComputeBackend.get_headers`; any name not present shall be rejected
  with HTTP 422 ("'<col>' is not a column in the uploaded CSV.") — this
  check applies uniformly to all four fields, not just `street_col`.
- **FR-2.6**: On successful validation, the system shall persist a
  `ColumnMapping(street_col, zip_col, city_col, country_col)` onto
  `session.mapping` and redirect back to `/mapping` (HTTP 303). (Per a
  code comment in `app/routers/mapping.py`, this redirect target changes to
  `/algorithm` once M2 adds the algorithm-selection step — see open
  question OQ-M2-1 in `acceptance-criteria/m2-fingerprint-algorithms.md`.)
- **FR-2.7**: If `GET /mapping` or `POST /mapping` is requested with no
  dataset in the session (`session.current_df is None`), the system shall
  redirect to `/` (HTTP 303).

## FR-3 — Algorithm Selection (M2, planned)

- **FR-3.1**: The system shall expose a registry of available matching
  algorithms (`app/algorithms/registry.py`, `ALGORITHM_REGISTRY`,
  `get_algorithm()`, `list_algorithms()`), each identified by a stable
  `key` and presenting a `label`, `family` (`AlgorithmFamily`, e.g.
  key-collision vs. nearest-neighbor), and a `param_specs` list describing
  its configurable parameters (`ParamSpec`).
- **FR-3.2**: `GET /algorithm` shall render a form letting the user choose
  one of the registered algorithms and, for the selected algorithm, its
  parameters (default values per `ParamSpec`).
- **FR-3.3**: As of M2, the registry shall contain exactly two algorithms,
  both key-collision family: Fingerprint (no parameters) and N-Gram
  Fingerprint (parameter `n`, default `2`).
- **FR-3.4**: `POST /algorithm` shall validate and persist the chosen
  algorithm key + params onto `session.algorithm_params`
  (`AlgorithmParams(algorithm_key, params)`), then trigger matching (see
  FR-4) and redirect/render to the results view.
- **FR-3.5 (M3, not yet built)**: Levenshtein Distance (parameter
  `threshold`, default `3`) and PPM/NCD (UI-displayed parameter
  `threshold`, default `3`, internally scaled `actual_threshold =
  ui_threshold / 10.0`) shall be added to the registry as nearest-neighbor
  family algorithms.

## FR-4 — Matching Execution (M2 partial, M3 complete)

- **FR-4.1**: `matching_service.run_matching(session, backend)` shall
  extract street addresses via
  `ComputeBackend.extract_street_addresses(frame, mapping)` (returning
  `dict[int, str]`), run the selected algorithm against that dict, and
  rebuild `session.candidate_pairs` from scratch on every invocation (no
  carry-over of prior accept/reject state across reruns).
- **FR-4.2 (M2 scope)**: For key-collision algorithms (Fingerprint, N-Gram
  Fingerprint), rows whose computed key collides are grouped into a
  cluster; clusters of size 1 (no collision partner) produce no candidate
  pair.
- **FR-4.3 (M2 scope)**: Algorithms must never receive or return a
  DataFrame — only `dict[int, str]` in, `AlgorithmOutput` (clusters or
  pairs) out — preserving the `compute/` vs `algorithms/` seam described in
  `CLAUDE.md`.
- **FR-4.4 (M3, not yet built)**: For nearest-neighbor algorithms
  (Levenshtein, NCD), rows shall first be partitioned into blocks
  (`compute_blocks`) and compared only within a block; resulting pairs
  under threshold are merged into clusters via union-find so both
  algorithm families render through the same results template.

## FR-5 — Results View (M2 read-only, M4 interactive)

- **FR-5.1 (M2 scope)**: `GET /results` shall render the current
  `session.candidate_pairs` (one row/group per cluster) as a read-only
  table: matched rows' street-address values, and (for nearest-neighbor
  results in later milestones) a distance value. Accept/reject controls
  shall be present in markup but inert (no working POST handler yet) per
  the M2 issue's explicit "checkboxes inert" instruction.
- **FR-5.2 (M4, not yet built)**: `POST
  /results/pair/{id}/accept|reject|representative` shall mutate that
  specific `CandidatePair`'s `status`/representative fields and return
  just that row's HTML fragment (no full-page reload), via HTMX.

## FR-6 — Merge and Rerun (M4, not yet built)

- **FR-6.1**: `merge_service.apply_merge(session, backend)` shall, for
  each `CandidatePair` with `status == "accepted"`, resolve a
  representative value (either the text of one of the matched original
  rows or user-supplied custom text), call
  `ComputeBackend.replace_values` to rewrite all matched rows' street
  value to that representative, append a new `DatasetVersion` with
  `created_from_merge=True`, and then call `run_matching` again so the
  results view reflects the merged data immediately.
- **FR-6.2**: `apply_merge` shall raise `ValueError` if no candidate pair
  has `status == "accepted"` at merge time.

## FR-7 — CSV Export (M5, not yet built)

- **FR-7.1**: `GET /export.csv` shall stream the current dataset version's
  data back as `text/csv` via `ComputeBackend.to_csv_bytes`, preserving
  string-typed columns (no leading-zero/NaN corruption) so the export
  round-trips with the same fidelity as the original upload.

## FR-8 — Session and Cookie Handling (shipped, M1, cross-cutting)

- **FR-8.1**: Each browser session shall be identified by an httponly,
  `samesite=lax` cookie named per `Settings.SESSION_COOKIE_NAME`
  (`"addressrefine_session"`), created on first request via
  `app.deps.get_session` and `SessionStore.get_or_create`.
- **FR-8.2**: Because most routes return `Response` objects directly
  (bypassing FastAPI's automatic dependency-response header merge), a
  fresh session id is propagated via `request.state.new_session_id` and
  applied to the actual outgoing response by `session_cookie_middleware`
  in `app/main.py`. Any new router added in future milestones gets this
  behavior automatically and requires no special handling.
