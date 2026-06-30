# Functional Requirements Document — AddressRefine

Status: Living document. Last revised: M4 BA pass (2026-06-30). Reflects
functionality shipped through M3, FR-9 (Visual Design System) from the
`chore/frontend-redesign-openrefine` chore, and a full rewrite of FR-3/FR-5/
FR-6 for M4's combined algorithm-and-results page scope (replacing the
earlier accept/reject/representative/pending-status plan). M5 is still
described at the level of detail available in the plan and will be filled
in/corrected when its BA pass runs.

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

## FR-3 — Algorithm Selection (M2 shipped; FR-3.5 added M3; FR-3.2/FR-3.4
restated, FR-3.6–FR-3.9 added M4 for the combined page)

- **FR-3.1**: The system shall expose a registry of available matching
  algorithms (`app/algorithms/registry.py`, `ALGORITHM_REGISTRY`,
  `get_algorithm()`, `list_algorithms()`), each identified by a stable
  `key` and presenting a `label`, `family` (`AlgorithmFamily`, e.g.
  key-collision vs. nearest-neighbor), and a `param_specs` list describing
  its configurable parameters (`ParamSpec`).
- **FR-3.2 (restated M4)**: `GET /algorithm` shall render a single combined
  page (algorithm/parameter controls plus the live results table — see
  FR-5) modeled on `docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`.
  The page presents:
  - a **Method** field choosing between "Nearest Neighbor" (maps to
    `AlgorithmFamily.NEAREST_NEIGHBOR`) and "Fingerprint" (maps to
    `AlgorithmFamily.KEY_COLLISION`);
  - a **Distance function** field whose options are filtered by the chosen
    Method: Nearest Neighbor offers "Levenshtein" / "PPM (NCD)"; Fingerprint
    offers "Fingerprint" / "N-Gram Fingerprint" (i.e. the four
    `ALGORITHM_REGISTRY` entries, regrouped into a two-level Method ->
    Distance function selection rather than M2/M3's flat single-select);
  - a parameter field whose presence/label depends on the chosen distance
    function (see FR-3.3 below).
- **FR-3.3 (M4)**: The parameter field accompanying the Distance function
  selector is:
  - labeled **"Radius"** for Levenshtein or PPM/NCD — this is the existing
    `threshold` parameter (`ParamSpec.name == "threshold"`); only the
    displayed `ParamSpec.label` text changes (to `"Radius"`), not the
    parameter name, semantics, or valid range;
  - **omitted entirely** for Fingerprint (it has no `param_specs`, so no
    field is rendered — not just hidden via CSS/Jinja conditional but
    structurally absent from the form for that selection, consistent with
    FR-3.2's filtering);
  - labeled **"N-Gram size"** for N-Gram Fingerprint — the existing `n`
    parameter; only `ParamSpec.label` changes (to `"N-Gram size"`).
- **FR-3.4 (restated M4)**: Any change to Method, Distance function, or the
  parameter field shall trigger an HTMX request that re-validates and
  persists the choice onto `session.algorithm_key` / `session.algorithm_params`,
  runs matching (see FR-4), and swaps in a refreshed results-table partial
  (FR-5) **in place, with no full-page reload and no explicit submit
  button** for this live-recompute path. (The legacy M2/M3 behavior of a
  `POST /algorithm` form submit redirecting to a separate `/results` page
  no longer exists as of M4 — see FR-3.9.) Per-distance-function validation
  rules are unchanged from M2/M3: `n >= 1` for N-Gram Fingerprint;
  `threshold >= 0` (int, displayed as "Radius") for Levenshtein; `threshold`
  in `[1, 10]` (int, displayed as "Radius") for PPM/NCD. Invalid params
  re-render the form/table fragment with HTTP 422 and a flash error without
  persisting or running matching.
- **FR-3.5 (M3)**: Levenshtein Distance (key `"levenshtein"`, label
  `"Levenshtein Distance"`, parameter `threshold` default `3`, valid range
  `>= 0`) and PPM/NCD (key `"ncd"`, label `"PPM / NCD"`, parameter
  `threshold` default `3`, valid UI range `[1, 10]`, internally scaled to
  `ui_threshold / 10.0`) shall be added to the registry as
  `AlgorithmFamily.NEAREST_NEIGHBOR` algorithms. (`ParamSpec.label` for
  `threshold` is updated to `"Radius"` by FR-3.3 above — a display-only
  change, the algorithm/registry semantics from M3 are otherwise
  unchanged.)
- **FR-3.6 (M4)**: As of M2, the registry shall contain exactly two
  algorithms, both key-collision family: Fingerprint (no parameters) and
  N-Gram Fingerprint (parameter `n`, default `2`). *(Renumbered from the
  former FR-3.3, unchanged in substance.)*
- **FR-3.7 (M4)**: `GET /algorithm` (the combined page) is the single entry
  point for both algorithm selection and result review. `GET /results` no
  longer renders an independent page; `GET /results` shall instead respond
  with an HTTP redirect to `/algorithm` (see FR-5.1).
- **FR-3.8 (M4)**: `app/static/js/match.js` (the project's first
  hand-written client-side JS file) shall handle purely client-side
  interactions that do not require a server round-trip: defaulting "New
  cell value" when "Merge?" is checked without clicking an address (FR-5.4),
  and setting "New cell value" + auto-checking "Merge?" when an address is
  clicked (FR-5.5). The live-recompute triggered by changing Method/
  Distance function/Radius/N-Gram size remains HTMX-driven (FR-3.4), not a
  manual `fetch()` call from `match.js`.
- **FR-3.9 (M4)**: The previously-planned `GET /algorithm/params` HTMX
  param-fragment endpoint (referenced in the original project plan) is
  superseded by FR-3.4's broader live-recompute behavior — changing Method
  or Distance function re-renders both the parameter field and the results
  table together in one HTMX swap, not the parameter field alone via a
  separate endpoint.

## FR-4 — Matching Execution (M2 partial; M3 completes NN path; M4 drops
transitive clustering)

- **FR-4.1**: `matching_service.run_matching(session)` shall extract street
  addresses via `ComputeBackend.extract_street_addresses(frame, mapping)`
  (returning `dict[int, str]`), run the selected algorithm, and rebuild
  `session.candidate_pairs` from scratch on every invocation (no carry-over
  of prior merge-checkbox state across reruns — see FR-6's "no state across
  recomputes" rule). Each resulting `CandidatePair` is assigned a unique
  `pair_id` (uuid4 string) at construction time (M3).
- **FR-4.2 (M2 scope, shipped; reconfirmed M4)**: For key-collision
  algorithms (Fingerprint, N-Gram Fingerprint), rows whose computed key
  collides are grouped into a same-key cluster of size >= 2; as of M4, every
  pairwise combination within such a cluster is exploded into its own
  `CandidatePair` (see FR-4.4) — clusters of size 1 still produce no pair,
  but clusters of size >= 3 now produce `C(n, 2)` pairs rather than one
  multi-member group.
- **FR-4.3 (M2 scope, shipped)**: Algorithms must never receive or return a
  DataFrame — only `dict[int, str]` in, `AlgorithmOutput` (clusters or
  pairs) out. No file under `app/algorithms/` may import `pandas`.
- **FR-4.4 (M3 introduced; superseded M4 — transitive clustering removed)**:
  For nearest-neighbor algorithms (Levenshtein, NCD), `run_matching` shall
  call `ComputeBackend.extract_columns(frame, mapping)` to obtain per-row
  zip and city values, pass the result to `compute_blocks` (see FR-4.5) to
  partition rows into blocks, then run the NN algorithm (which compares
  only within-block pairs). **As of M4, each entry in
  `AlgorithmOutput.pairs` becomes its own `CandidatePair` directly** — the
  `_UnionFind`-based transitive-clustering step used in M3 is removed
  entirely, so `CandidatePair.row_indices` is always exactly length 2 for
  NN-family pairs. This is a **deliberate reversal of the M3 product
  decision** "multi-pair cluster distance = max pairwise distance"
  (previously documented in this project's working notes); see
  `acceptance-criteria/m4-merge-review.md`'s Open Questions / Decisions
  section for the explicit rationale. The `distance` field of each
  NN-family `CandidatePair` is the single pairwise distance returned by the
  algorithm for that pair (no longer a cluster maximum, since there is no
  longer a cluster). Key-collision algorithms continue to receive
  `blocks=None`; their pairs (FR-4.2) carry `distance=None` since no
  distance check applies — same-key equality is itself the match
  condition.
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

## FR-5 — Results View (M2 read-only; M3 adds distance scale label; M4
rewrite — merged into the combined page as a live, pairwise, editable table)

- **FR-5.1 (M4 rewrite — full replacement of the M2/M3 behavior)**: A
  dedicated full-page `GET /results` route no longer exists as of M4. The
  live results table is rendered as part of `GET /algorithm` (FR-3.2) and
  refreshed in place by the HTMX live-recompute (FR-3.4). For backward
  compatibility with bookmarked/typed URLs, `GET /results` shall respond
  with an HTTP redirect (303) to `/algorithm` rather than 404ing or
  rendering its own page.
- **FR-5.2 (M4)**: The results table shall render exactly one row per
  `CandidatePair` in `session.candidate_pairs`, and **every `CandidatePair`
  is exactly one pair of two addresses** (`len(row_indices) == 2`) — never
  a multi-member cluster (see FR-4.2/FR-4.4). Each row displays:
  - a **"Merge?"** checkbox (unchecked by default on every fresh
    render/recompute — no carried-over checked state, consistent with
    FR-4.1's "rebuilt from scratch" rule);
  - the two candidate addresses, each individually clickable;
  - an editable **"New cell value"** free-text input (FR-5.3);
  - a **"Distance"** column showing the pair's numeric distance, shown only
    for nearest-neighbor-family pairs; this column (or its cell content) is
    omitted for fingerprint-family pairs, which carry no numeric distance
    by construction (FR-4.4's `distance=None`).
- **FR-5.3 (M4)**: "New cell value" is pre-filled per the interaction rules
  in FR-5.4/FR-5.5 but remains a free-text editable `<input>` at all times
  — the user may type any arbitrary value into it before merging, not just
  one of the two candidate addresses shown in that row.
- **FR-5.4 (M4)**: Checking a row's "Merge?" checkbox without having
  clicked either address in that row shall default "New cell value" to
  that row's first-listed address (i.e. the first element of
  `row_indices`'/`row.rows[0]`'s street value, in the order the row was
  rendered). This is a client-side-only behavior (`app/static/js/match.js`,
  FR-3.8) — no server round-trip.
- **FR-5.5 (M4)**: Clicking either address displayed in a row shall (a) set
  "New cell value" to that address's text and (b) auto-check that row's
  "Merge?" checkbox, regardless of its prior state. Also client-side-only
  (`match.js`).
- **FR-5.6 (M4)**: There is no per-pair accept/reject/dismiss action and no
  persisted pair status of any kind (this supersedes the FR-5.2 in the
  pre-M4 FRD, which referenced a `POST /results/pair/{id}/accept|reject|
  representative` endpoint that is **not built** — see
  `data-dictionary.md` for the dropped `status`/`representative_*` fields).
  The only mutating action available from this page is the single
  "Merge selected & re-cluster" button (FR-6).

## FR-6 — Merge and Rerun (M4 full rewrite — replaces the accept/reject
+ representative-selection plan referenced by the pre-M4 FRD)

- **FR-6.1**: A single **"Merge selected & re-cluster"** button (no
  Select-all / Deselect-all / Export-clusters / Close buttons — those
  OpenRefine-dialog extras are explicitly out of scope for AddressRefine)
  shall submit all checked rows' current pair id + current "New cell
  value" text to the merge endpoint.
- **FR-6.2**: `merge_service.apply_merge(session, backend, merge_requests)`
  shall, for every **checked** row submitted (no `status` field is read or
  written — there is no accept/reject/pending model as of M4), rewrite
  **both** underlying dataset rows in that pair (`row_indices[0]` and
  `row_indices[1]`) to that row's submitted "New cell value" via
  `ComputeBackend.replace_values`, not just the non-matching side — this is
  idempotent for whichever side already equals the target value.
- **FR-6.3 — Conflict detection (final, resolved)**: Before any mutation is
  applied, `apply_merge` shall check whether any underlying dataset row
  index is targeted by two or more checked rows with **different** "New
  cell value" texts (e.g. pair A-B checked with value `"B"` and pair A-C
  checked with value `"C"` both target row A but disagree). If any such
  conflict exists, the merge is **blocked entirely**: no row is mutated, no
  `DatasetVersion` is appended, and the response surfaces a validation
  error listing every conflicting row index and its disagreeing target
  values, so the user can fix their checkbox/text-field selections and
  resubmit. This is a hard block, not a silent last-write-wins or
  first-write-wins resolution.
- **FR-6.4**: If no conflicts are detected and at least one row was
  checked, `apply_merge` shall apply all rewrites, append a new
  `DatasetVersion` with `created_from_merge=True` (`version = previous + 1`
  per `data-dictionary.md`'s `DatasetVersion.version` note), and then call
  `run_matching` again — using the algorithm/params currently selected at
  merge time, not the defaults — so the results table reflects the merged
  data immediately on the same combined page.
- **FR-6.5**: If zero rows were checked, clicking "Merge selected &
  re-cluster" is a no-op: no `ValueError`, no version append, no rerun, no
  validation error — the page/table is simply unchanged. (This differs
  from the pre-M4 FRD's FR-6.2, which specified `apply_merge` raising
  `ValueError` on an empty accepted set under the old accept/reject model;
  under the M4 model, "nothing checked" is a normal, harmless idle state of
  a live table rather than an erroneous submit action.)

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

## FR-9 — Visual Design System (chore: `chore-frontend-redesign`, shipped)

Source: `docs/design/ui-design-spec.md` (OpenRefine-derived visual language),
GitHub issue #10. This is a process/visual chore, not a numbered milestone —
see `CLAUDE.md`'s Workflow section, chore-loop variant. Scope is explicitly
"visual only, current structure": **at the time this chore shipped**, the
4-screen wizard (`upload.html`, `mapping.html`, `algorithm.html`,
`results.html`) kept its existing routes, forms, and field names; only CSS
custom properties, class names, and markup *wrapper* structure changed.
M4 (FR-3/FR-5/FR-6 above) subsequently merges `algorithm.html` and
`results.html` into one combined page and extends the component system
with new interactive elements (per-row checkbox, editable "New cell value"
input, merge action bar) that did not exist when this chore's FR-9.1–FR-9.8
below were written — those component classes/tokens remain the visual
foundation M4 builds on, not a description of the current page count.
Historical detail below is left as-shipped: at the time, only CSS custom
properties, class names, and markup *wrapper* structure (e.g. grouping
existing fields into `.control-row`/`.control-group` containers) changed.

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
