# Functional Requirements Document — AddressRefine

Status: Living document. Last revised: `chore-frontend-redesign` BA pass
(2026-06-29). Reflects functionality shipped through M3 plus M3 requirements
fully specified, plus FR-9 (Visual Design System) added for the
`chore/frontend-redesign-openrefine` chore; M4-M5 are described at the level
of detail available in the plan and will be filled in/corrected as each
milestone's BA pass runs.

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

## FR-2 — Column Mapping (shipped, M1; FR-2.6 redirect target updated M2)

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
  `session.mapping` and redirect to `/algorithm` (HTTP 303). (Redirect
  target updated from `/mapping` to `/algorithm` in M2 per OQ-M2-1;
  see `acceptance-criteria/m2-fingerprint-algorithms.md` AC-M2-24.)
- **FR-2.7**: If `GET /mapping` or `POST /mapping` is requested with no
  dataset in the session (`session.current_df is None`), the system shall
  redirect to `/` (HTTP 303).

## FR-3 — Algorithm Selection (M2 shipped; FR-3.5 added M3)

- **FR-3.1**: The system shall expose a registry of available matching
  algorithms (`app/algorithms/registry.py`, `ALGORITHM_REGISTRY`,
  `get_algorithm()`, `list_algorithms()`), each identified by a stable
  `key` and presenting a `label`, `family` (`AlgorithmFamily`, e.g.
  key-collision vs. nearest-neighbor), and a `param_specs` list describing
  its configurable parameters (`ParamSpec`).
- **FR-3.2**: `GET /algorithm` shall render a form letting the user choose
  one of the registered algorithms and, for the selected algorithm, its
  parameters (default values per `ParamSpec`). As of M3, the form shall
  also include a `threshold` input field shown/hidden via Jinja conditional
  based on algorithm family (visible for NN algorithms, hidden for
  key-collision algorithms).
- **FR-3.3**: As of M2, the registry shall contain exactly two algorithms,
  both key-collision family: Fingerprint (no parameters) and N-Gram
  Fingerprint (parameter `n`, default `2`).
- **FR-3.4**: `POST /algorithm` shall validate and persist the chosen
  algorithm key + params onto `session.algorithm_params`, then trigger
  matching (see FR-4) and redirect to `/results` (HTTP 303). Per-algorithm
  validation rules: `n >= 1` for N-Gram Fingerprint (M2); `threshold >= 0`
  (int) for Levenshtein; `threshold` in `[1, 10]` (int) for NCD (M3).
  Invalid params render the form again with HTTP 422 and a flash error
  without persisting or running matching.
- **FR-3.5 (M3)**: Levenshtein Distance (key `"levenshtein"`, label
  `"Levenshtein Distance"`, parameter `threshold` default `3`, valid range
  `>= 0`) and PPM/NCD (key `"ncd"`, label `"PPM / NCD"`, parameter
  `threshold` default `3`, valid UI range `[1, 10]`, internally scaled to
  `ui_threshold / 10.0`) shall be added to the registry as
  `AlgorithmFamily.NEAREST_NEIGHBOR` algorithms.

## FR-4 — Matching Execution (M2 partial; M3 completes NN path)

- **FR-4.1**: `matching_service.run_matching(session)` shall extract street
  addresses via `ComputeBackend.extract_street_addresses(frame, mapping)`
  (returning `dict[int, str]`), run the selected algorithm, and rebuild
  `session.candidate_pairs` from scratch on every invocation (no carry-over
  of prior accept/reject state across reruns). Each resulting `CandidatePair`
  is assigned a unique `pair_id` (uuid4 string) at construction time (M3).
- **FR-4.2 (M2 scope, shipped)**: For key-collision algorithms (Fingerprint,
  N-Gram Fingerprint), rows whose computed key collides are grouped into a
  cluster; clusters of size 1 produce no candidate pair.
- **FR-4.3 (M2 scope, shipped)**: Algorithms must never receive or return a
  DataFrame — only `dict[int, str]` in, `AlgorithmOutput` (clusters or
  pairs) out. No file under `app/algorithms/` may import `pandas`.
- **FR-4.4 (M3)**: For nearest-neighbor algorithms (Levenshtein, NCD),
  `run_matching` shall call `ComputeBackend.extract_columns(frame, mapping)`
  to obtain per-row zip and city values, pass the result to `compute_blocks`
  (see FR-4.5) to partition rows into blocks, then run the NN algorithm
  (which compares only within-block pairs), convert the resulting
  `AlgorithmOutput.pairs` into clusters via union-find, and build one
  `CandidatePair` per cluster. The `distance` field of each `CandidatePair`
  shall be set to the maximum pairwise distance among all members of that
  cluster. Key-collision algorithms continue to receive `blocks=None`.
- **FR-4.5 (M3)**: `algorithms/blocking.py` shall expose
  `compute_blocks(rows: dict[int, dict[str, str]]) -> dict[str, list[int]]`.
  Block key construction: if the row's `"zip"` value is non-blank after
  stripping whitespace and lowercasing, the block key is the first 3
  characters of that normalized zip (or the full string if shorter than 3
  characters). Otherwise, if `"city"` is non-blank after normalization, the
  block key is the normalized city string. Otherwise, the block key is
  `"__unblocked__"`. This function is a pure function over plain dicts —
  it does not import `pandas` or receive a `ColumnMapping`.
- **FR-4.6 (M3)**: `algorithms/ncd.py` shall expose
  `normalized_compression_distance(a: str, b: str) -> float` using
  `bz2.compress` lengths with both concatenation orders averaged for
  symmetry: `((C(a+b)-min(Ca,Cb))/max(Ca,Cb) + (C(b+a)-min(Ca,Cb))/max(Ca,Cb)) / 2`.
  Two empty strings shall return `0.0`. This function is used internally by
  `NCDAlgorithm` and may be used independently in tests.
- **FR-4.7 (M3)**: `LevenshteinNNAlgorithm` shall use
  `rapidfuzz.distance.Levenshtein.distance(a, b, score_cutoff=threshold)`
  for efficiency. Pairs where the distance exceeds `threshold` are not
  included in `AlgorithmOutput.pairs`. Comparisons are only performed
  within the blocks provided by the `blocks` argument.

## FR-5 — Results View (M2 read-only; M3 adds distance scale label; M4 interactive)

## FR-5 — Results View (M2 read-only; M3 adds distance scale label; M4 interactive)

- **FR-5.1 (M2 shipped; M3 extends)**: `GET /results` shall render the
  current `session.candidate_pairs` (one row/group per cluster) as a
  read-only table: matched rows' street-address values, a distance column,
  and inert accept/reject controls. As of M3, when the current algorithm is
  a nearest-neighbor algorithm, the page shall display a scale sub-label
  near the "Distance" column header: `"edit distance"` for Levenshtein and
  `"NCD score (0–1)"` for NCD. For key-collision algorithms (Fingerprint,
  N-Gram Fingerprint), no sub-label is shown and distance continues to
  render as `"—"` per pair.
- **FR-5.2 (M4, not yet built)**: `POST
  /results/pair/{id}/accept|reject|representative` shall mutate that
  specific `CandidatePair`'s `status`/representative fields (using
  `pair_id` from M3 to address the pair) and return just that row's HTML
  fragment (no full-page reload), via HTMX.

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

## FR-9 — Visual Design System (chore: `chore-frontend-redesign`, not yet built)

Source: `docs/design/ui-design-spec.md` (OpenRefine-derived visual language),
GitHub issue #10. This is a process/visual chore, not a numbered milestone —
see `CLAUDE.md`'s Workflow section, chore-loop variant. Scope is explicitly
"visual only, current structure": the 4-screen wizard (`upload.html`,
`mapping.html`, `algorithm.html`, `results.html`) keeps its existing routes,
forms, and field names; only CSS custom properties, class names, and markup
*wrapper* structure (e.g. grouping existing fields into `.control-row`/
`.control-group` containers) change.

- **FR-9.1**: `app/static/css/styles.css` shall define, under `:root`, at
  least the following CSS custom properties with the values specified in
  `docs/design/ui-design-spec.md`'s Palette table: `--color-bg`,
  `--color-surface`, `--color-header-bg`, `--color-header-border`,
  `--color-text`, `--color-border`, `--color-primary`,
  `--color-primary-hover`, `--color-secondary-bg`,
  `--color-table-header-bg`, `--color-table-row-odd`,
  `--color-table-row-even`, `--color-muted`, `--color-link`.
- **FR-9.2**: `app/static/css/styles.css` shall define spacing custom
  properties `--space-xs`, `--space-sm`, `--space-md`, `--space-lg`,
  `--space-xl` per the ui-design-spec's Spacing scale table, and existing
  hard-coded rem-based gap/padding/margin values in component rules shall be
  expressed in terms of these tokens rather than as new bare literals.
- **FR-9.3**: No template under `app/templates/` (including `partials/`)
  shall contain an inline `style="..."` attribute. All visual styling is
  expressed via CSS classes in `styles.css` (statically verifiable by
  grepping `app/templates/**/*.html` for `style=`).
- **FR-9.4**: `base.html`'s `.site-header` shall use `--color-header-bg`
  for its background and `--color-header-border` for its bottom border
  (replacing the current plain-white header background), per the
  ui-design-spec's Palette table.
- **FR-9.5**: `mapping.html` and `algorithm.html` shall wrap their existing
  form fields in `.control-row` / `.control-group` container `<div>`s per
  the ui-design-spec's Layout pattern section, without changing any
  `name=`, `id=`, validation, or POST-target attributes on the underlying
  `<label>`/`<select>`/`<input>` elements.
- **FR-9.6**: All submit buttons across the 4 screens ("Upload", "Save
  mapping", "Run matching") shall carry the `.btn` and `.btn-primary`
  classes defined in `styles.css` per the ui-design-spec's Button styling
  table, replacing the current bare-`button`-selector styling.
- **FR-9.7**: `.results-table` shall apply header-row shading
  (`--color-table-header-bg`), alternating zebra-striped body rows
  (`--color-table-row-odd` / `--color-table-row-even` via
  `tr:nth-child(odd)`/`tr:nth-child(even)`), and a row-hover background,
  per the ui-design-spec's Table styling section.
- **FR-9.8**: The inert `Accept`/`Reject` buttons in
  `partials/_pair_row.html` shall carry `.btn` plus a visible `:disabled`
  treatment (reduced opacity, muted text color) per the ui-design-spec's
  Button styling table, distinguishing them visually from an enabled
  primary button even though they remain non-functional until M4.
- **FR-9.9 (qualitative, not code-checkable)**: The overall visual
  impression of all 4 screens — palette, typography scale, table/button
  shapes — shall be judged by the `tester` agent's Visual QA pass
  (Playwright screenshots compared against
  `docs/design/reference/screenshots/`) as "reasonably faithful" to the
  OpenRefine reference material, per `.claude/agents/tester.md`'s
  Visual — Must fix / Visual — Informational split. This requirement is
  intentionally subjective; FR-9.1 through FR-9.8 above carry the
  objective, automatable portion of this chore's acceptance bar.
