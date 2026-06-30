# Acceptance Criteria — M4: Combined Algorithm/Results Page + Pairwise Merge

Milestone branch: `m4-merge-review`
Status: Written before the `coder` pass. Source: GitHub issue #3 (title:
"M4: Accept/reject, representative selection, merge + rerun" — see "Plan
drift" note below), the M4 scope redesign worked out via direct user Q&A
with the orchestrating session (accept/reject/pending-status plan
discarded in favor of a live pairwise merge-review table modeled on
OpenRefine's cluster/merge dialog), and
`docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`. Each
AC is in Given/When/Then form and is written to be directly convertible to
a test case by the `tester` agent. See `traceability-matrix.md` for the
expected test file/case mapping.

**Plan/issue drift note**: GitHub issue #3 ("M4: Accept/reject,
representative selection, merge + rerun") describes the original
accept/reject/representative-selection design from the project plan. That
design is **superseded in full** by the scope below — there is no
`status`/`representative_mode` field, no `POST /results/pair/{id}/accept|
reject|representative` endpoint, and no separate `/results` page. The
orchestrating session is expected to update issue #3's body to reflect this
before the `coder` pass starts (BA does not edit GitHub directly).

---

## Combined page structure — `GET /algorithm`

### AC-M4-1 — `GET /algorithm` renders a Method field with two options

**Given** a session with a confirmed mapping,
**When** `GET /algorithm` is requested,
**Then** the rendered page contains a "Method" form control offering
exactly two options: "Nearest Neighbor" (mapping to
`AlgorithmFamily.NEAREST_NEIGHBOR`) and "Fingerprint" (mapping to
`AlgorithmFamily.KEY_COLLISION`).

### AC-M4-2 — Distance function options are filtered by the selected Method

**Given** "Nearest Neighbor" is the selected Method,
**When** the page (or its HTMX-refreshed fragment) is rendered,
**Then** the "Distance function" field offers exactly "Levenshtein" and
"PPM (NCD)" as options (mapping to algorithm keys `"levenshtein"` and
`"ncd"`).

**Given** "Fingerprint" is the selected Method,
**When** the page (or its HTMX-refreshed fragment) is rendered,
**Then** the "Distance function" field offers exactly "Fingerprint" and
"N-Gram Fingerprint" as options (mapping to algorithm keys
`"fingerprint"` and `"ngram_fingerprint"`).

### AC-M4-3 — Parameter field is labeled "Radius" for Levenshtein/NCD

**Given** "Levenshtein" or "PPM (NCD)" is the selected Distance function,
**When** the page is rendered,
**Then** a parameter input field labeled "Radius" is shown, bound to the
existing `threshold` parameter (same name, same valid range, same default
as M3: Levenshtein `>= 0` default `3`; NCD `[1, 10]` default `3`) — only
the displayed label text changes from M3's "Max edit distance"/"Similarity
threshold (1–10)".

### AC-M4-4 — No parameter field at all for plain Fingerprint

**Given** "Fingerprint" is the selected Distance function,
**When** the page is rendered,
**Then** no parameter input field is rendered for it (Fingerprint has no
`param_specs`) — the field is structurally absent, not merely hidden via
CSS, consistent with how the other distance functions structurally swap
in/out.

### AC-M4-5 — Parameter field is labeled "N-Gram size" for N-Gram Fingerprint

**Given** "N-Gram Fingerprint" is the selected Distance function,
**When** the page is rendered,
**Then** a parameter input field labeled "N-Gram size" is shown, bound to
the existing `n` parameter (same name, same valid range `>= 1`, same
default `2` as M2) — only the displayed label text changes.

---

## Live recompute (HTMX) — no submit button

### AC-M4-6 — Changing Method triggers a live recompute

**Given** the combined page is loaded with some Method/Distance
function/param selection and a non-empty results table,
**When** the user changes the Method field,
**Then** an HTMX request fires automatically (no separate submit button
click required), the server re-runs matching with the newly implied
default Distance function for that Method, and returns a refreshed
results-table partial that replaces the table in place without a full page
reload.

### AC-M4-7 — Changing Distance function triggers a live recompute

**Given** the combined page is loaded,
**When** the user changes the Distance function field (Method held
constant),
**Then** an HTMX request fires automatically, matching reruns with the
newly selected algorithm and its default/current parameter value, and the
results-table partial refreshes in place.

### AC-M4-8 — Changing Radius or N-Gram size triggers a live recompute

**Given** the combined page is loaded with Levenshtein, NCD, or N-Gram
Fingerprint selected,
**When** the user changes the Radius or N-Gram size field's value,
**Then** an HTMX request fires automatically, matching reruns with the new
parameter value, and the results-table partial refreshes in place.

### AC-M4-9 — Invalid Radius/N-Gram size value is rejected without crashing the live table

**Given** the combined page is loaded,
**When** the user enters an invalid Radius (e.g. negative for Levenshtein,
`0` or `> 10` for NCD) or an invalid N-Gram size (e.g. `0` or non-integer),
**Then** the HTMX response is HTTP 422 with a flash/inline error message,
`session.algorithm_params` is not updated, `run_matching` is not invoked,
and the previously-valid results table is not silently discarded (the
error is shown without corrupting prior state).

### AC-M4-10 — `GET /results` redirects to `/algorithm`

**Given** any session state,
**When** `GET /results` is requested,
**Then** the response is an HTTP redirect (303) to `/algorithm`, not a
404 and not an independently rendered page.

---

## Pairwise candidate generation — `matching_service`

### AC-M4-11 — A key-collision cluster of 3 explodes into exactly 3 pairs

**Given** three rows A, B, C whose computed fingerprint (or n-gram
fingerprint) keys are all identical (i.e. they would have formed one
3-member cluster under M2/M3's clustering model),
**When** `run_matching(session)` is called with a key-collision algorithm
selected,
**Then** `session.candidate_pairs` contains exactly 3 entries — one for
each pairwise combination (A-B, A-C, B-C) — and no entry has more than 2
elements in `row_indices`.

### AC-M4-12 — Key-collision pair `distance` is `None`

**Given** any `CandidatePair` produced by a key-collision algorithm,
**Then** its `distance` field is `None` (same-key equality is the match
condition; there is no numeric distance to report).

### AC-M4-13 — Transitive nearest-neighbor matches produce separate pairs, not one cluster

**Given** three rows A, B, C where A-B and B-C are each within the
configured Radius but A-C is not (the classic transitive-clustering
fixture used in M3's AC-M3-26/Scenario 7),
**When** `run_matching(session)` is called with Levenshtein or NCD
selected,
**Then** `session.candidate_pairs` contains exactly 2 entries (A-B and
B-C), each with `row_indices` of length 2 — **not** one 3-member cluster,
and **not** a synthesized A-C pair (A and C were never directly within
radius of each other, and no out-of-radius pair is ever shown).

### AC-M4-14 — Nearest-neighbor pair `distance` is the single pairwise value, not a cluster maximum

**Given** a pair A-B with measured distance `d(A,B) = 2.0` returned
directly by the algorithm's `AlgorithmOutput.pairs`,
**When** `run_matching` constructs the corresponding `CandidatePair`,
**Then** `pair.distance == 2.0` exactly — not adjusted, maximized, or
aggregated against any other pair's distance (this is a deliberate
reversal of M3's "cluster distance = max pairwise distance" rule; see
"M3 reversal" note below).

### AC-M4-15 — Every `CandidatePair.row_indices` has exactly 2 elements

**Given** any successful `run_matching` call, regardless of which of the
four algorithms (Fingerprint, N-Gram Fingerprint, Levenshtein, NCD) is
selected,
**Then** every entry in `session.candidate_pairs` has
`len(row_indices) == 2`. (Parametrized check across all four algorithms.)

### AC-M4-16 — `run_matching` rebuilds `candidate_pairs` from scratch; no "checked" state survives a recompute

**Given** a session whose results table has some rows' "Merge?" checkboxes
checked in the rendered HTML from a prior recompute,
**When** the user changes Method/Distance function/Radius/N-Gram size and
the live recompute fires,
**Then** `session.candidate_pairs` is fully replaced (new `pair_id`s, no
correlation attempted with the prior render's checked state) and the
freshly rendered table has every "Merge?" checkbox unchecked by default —
there is no mechanism that preserves a checked state across a recompute.

---

## Results table — rendering, columns, interaction affordances

### AC-M4-17 — Every row's "Merge?" checkbox is unchecked on render

**Given** any results-table render (full page or HTMX partial),
**Then** every row's "Merge?" `<input type="checkbox">` is unchecked
(`checked` attribute absent) — there is no server-driven default-checked
state.

### AC-M4-18 — Distance column shown for NN pairs, omitted for fingerprint-family pairs

**Given** a results table where some rows came from a nearest-neighbor
algorithm run and (in a separate render) some came from a key-collision
algorithm run,
**Then** for nearest-neighbor-family rows, a numeric "Distance" value is
rendered; for fingerprint-family rows, no numeric distance is rendered for
that row/cell (omitted, not rendered as "0" or "—" — distinguish from
M2/M3's "—" placeholder, since M4 doesn't even attempt to show a Distance
column value as meaningful for these rows).

### AC-M4-19 — Each row renders both candidate addresses as individually clickable elements

**Given** any results-table row,
**Then** both of the pair's two addresses are rendered as separate
clickable elements (e.g. `<button>`/clickable `<span>` — exact element
choice left to the `coder` pass) distinguishable from each other and from
the row's other controls, each carrying enough data (e.g. a `data-*`
attribute with the address text and/or row index) for `match.js` to read
on click.

### AC-M4-20 — "New cell value" input is not readonly or disabled

**Given** any results-table row,
**Then** its "New cell value" `<input>` does not carry a `readonly` or
`disabled` attribute — it is always directly user-editable regardless of
whether "Merge?" is checked or an address has been clicked.

---

## Client-side interactions — `app/static/js/match.js`

### AC-M4-21 — Checking "Merge?" without clicking an address defaults "New cell value" to the first-listed address

**Given** a row whose "New cell value" input is currently empty (or holds
its initial empty/default state) and neither address has been clicked,
**When** the user checks that row's "Merge?" checkbox,
**Then** "New cell value" is set to the row's first-listed address text
(the first element in rendering order), purely client-side (no network
request).

### AC-M4-22 — Clicking either address sets "New cell value" and auto-checks "Merge?"

**Given** any results-table row in any checkbox state,
**When** the user clicks either of the row's two displayed addresses,
**Then** "New cell value" is set to that clicked address's text and the
row's "Merge?" checkbox becomes checked (regardless of its prior state),
purely client-side.

### AC-M4-23 — "New cell value" remains editable after being defaulted/clicked

**Given** a row whose "New cell value" was just set by AC-M4-21 or
AC-M4-22,
**When** the user types a different value into "New cell value",
**Then** the input accepts and reflects the typed value (it is not reset
or overwritten by any subsequent unrelated interaction), and "Merge?"
remains checked.

### AC-M4-24 — No per-pair accept/reject endpoints exist

**Given** the M4 deliverable,
**Then** there is no `POST /results/pair/{id}/accept`,
`POST /results/pair/{id}/reject`, or
`POST /results/pair/{id}/representative` route registered on the FastAPI
app (statically verifiable via the app's route table) — the only
mutating route reachable from the results table is `POST /merge`.

---

## Merge — `merge_service.apply_merge`

### AC-M4-25 — Checked pair's both rows rewritten to "New cell value"

**Given** a checked pair A-B with "New cell value" = `"X"`,
**When** `apply_merge` is called with this pair included in the merge
request,
**Then** both row A's and row B's underlying street value are rewritten
to `"X"` via `ComputeBackend.replace_values` — not just the side that
didn't already equal `"X"`.

### AC-M4-26 — Merge is idempotent when one side already equals the target value

**Given** a checked pair A-B where row A's street value is already `"X"`
and "New cell value" = `"X"`,
**When** `apply_merge` is called,
**Then** row A's value is unchanged (still `"X"`) and row B's value
becomes `"X"`; no error occurs from row A "already matching."

### AC-M4-27 — Conflicting checked rows targeting the same underlying row block the merge entirely

**Given** two checked pairs that share an underlying row but disagree on
its target value — e.g. pair A-B checked with "New cell value" = `"B"`,
and pair A-C checked with "New cell value" = `"C"` (both target row A, one
wants `"B"`, the other wants `"C"`),
**When** `apply_merge` is called with both pairs included in the merge
request,
**Then** the merge is blocked: `apply_merge` does not call
`ComputeBackend.replace_values` at all, no `DatasetVersion` is appended,
and a validation error is raised/returned identifying the conflicting row
index and its disagreeing target values.

### AC-M4-28 — A blocked (conflicting) merge mutates nothing

**Given** the conflict scenario in AC-M4-27,
**When** `apply_merge` is called and raises/returns the conflict error,
**Then** `session.versions` is unchanged (same length, same `current_df`
identity/content as before the call) and `session.candidate_pairs` is
unchanged (no rerun of matching occurred).

### AC-M4-29 — Successful merge appends a new `DatasetVersion` with `created_from_merge=True`

**Given** a merge request with at least one checked pair and no conflicts,
**When** `apply_merge` succeeds,
**Then** `session.versions` gains exactly one new entry with
`version == previous_version.version + 1` and `created_from_merge ==
True`.

### AC-M4-30 — Successful merge reruns matching using the currently-selected algorithm and params

**Given** a session with `algorithm_key="levenshtein"` and
`algorithm_params={"threshold": 5}` at the time of a successful merge,
**When** `apply_merge` completes,
**Then** `run_matching` was invoked using that same algorithm
key/params (not reset to any default), so `session.candidate_pairs`
reflects a fresh Levenshtein run (threshold 5) against the newly merged
data.

### AC-M4-31 — Zero checked rows is a no-op

**Given** a merge request with zero checked pairs (the user clicked "Merge
selected & re-cluster" without checking anything),
**When** `apply_merge` is called,
**Then** no `ValueError`/exception is raised, no `DatasetVersion` is
appended, `run_matching` is not invoked, and `session.candidate_pairs` is
unchanged. (This differs deliberately from the M3-era plan's
"`apply_merge` raises `ValueError` if nothing accepted" — under the M4
model, an empty checked set is a normal idle state, not an error.)

---

## `POST /merge` router

### AC-M4-32 — Merge request includes only checked rows

**Given** a results table with some rows checked and some unchecked,
**When** the user submits "Merge selected & re-cluster",
**Then** the request payload `POST /merge` sends to the server includes
only the checked rows' `pair_id` + current "New cell value" text —
unchecked rows are not included as merge candidates (no explicit `checked:
false` entries needed).

### AC-M4-33 — Successful merge returns a refreshed results-table partial

**Given** a valid, non-conflicting merge request with >= 1 checked row,
**When** `POST /merge` completes successfully,
**Then** the response is (or triggers, via HTMX swap) a refreshed
results-table partial reflecting the post-merge, re-run candidate pairs —
the same combined page, no full-page navigation.

### AC-M4-34 — Conflicting merge request returns a validation error without mutating session state

**Given** a merge request that would trigger the conflict condition in
AC-M4-27,
**When** `POST /merge` is called,
**Then** the response communicates the conflict (e.g. HTTP 422/400 with a
flash/inline error listing the conflicting row(s) and their disagreeing
values) and `session.versions`/`session.candidate_pairs` are unchanged, as
in AC-M4-28.

---

## `ComputeBackend.replace_values` — real implementation

### AC-M4-35 — `replace_values` sets `street_col` at the given row indices to `new_value`

**Given** a loaded frame and a `street_col` name valid for that frame,
**When** `PandasComputeBackend.replace_values(frame, street_col,
row_indices, new_value)` is called with a list of row indices,
**Then** the returned frame has `new_value` at `street_col` for every
index in `row_indices`, and other rows/columns are unaffected.

### AC-M4-36 — `replace_values` no longer raises `NotImplementedError`

**Given** the M4 deliverable,
**When** `PandasComputeBackend.replace_values` is called with valid
arguments,
**Then** it does not raise `NotImplementedError` (supersedes M1's
AC-M1/`test_replace_values_raises_not_implemented`, which is expected to
be updated/replaced by the `tester` agent for M4, not left asserting stub
behavior against now-real code).

---

## No regression — visual design system (FR-9)

### AC-M4-37 — Merged `algorithm.html` still has no inline `style=` attributes

**Given** the M4-merged `algorithm.html` (combining the former
`algorithm.html` and `results.html` markup),
**Then** it contains no inline `style="..."` attribute anywhere, per the
existing FR-9.3 rule — re-verified because this template absorbed markup
from two prior templates that must continue using the existing
`.control-row`/`.control-group`/`.btn`/`.results-table` component classes
rather than reintroducing inline styles for the new merge-review controls.

---

## Open Questions

### Resolved by the scope brief (not re-litigated here; listed for traceability only)

| # | Topic | Resolution | Primary AC(s) |
|---|---|---|---|
| OQ-M4-S1 | Accept/reject/pending status model | Dropped entirely; "Merge?" checkbox + "Merge selected & re-cluster" is the only mutating action | AC-M4-24, data-dictionary.md |
| OQ-M4-S2 | Merge conflict handling | Blocked outright with a validation error; nothing mutated | AC-M4-27, AC-M4-28, AC-M4-34 |
| OQ-M4-S3 | Out-of-radius pairs | Never shown, achieved structurally (no transitive clustering for NN) rather than as a runtime filter | AC-M4-13 |
| OQ-M4-S4 | "New cell value" editability | Always an editable free-text input, pre-filled but never read-only | AC-M4-20, AC-M4-23 |

### Genuinely new, not covered by the resolved scope brief — needs a decision before/during the `coder` pass

1. **HTMX trigger granularity/debounce for the Radius/N-Gram size numeric
   field.** The scope brief says "any change... automatically and
   immediately recomputes." For a `<input type=number>`, should the HTMX
   trigger be `change` (fires on blur/stepper-click, avoiding a request per
   keystroke) or `input` with a debounce (more "live" but far more
   requests, and intermediate invalid values like an empty field mid-edit
   would otherwise fire requests)? Recommendation: `change` (matches
   typical HTMX number-input patterns and avoids spurious 422s on
   in-progress typing), but this is a UX-feel decision, not something the
   11 scope points pin down. **Flagged for the orchestrating session/coder
   to decide**, not blocking — default to `change` if not otherwise told.
2. **Wire format for the `POST /merge` request body.** The scope brief
   specifies the logical shape (checked pair_ids + their current "New cell
   value" text) but not the literal HTML form encoding — e.g. whether
   checked rows are submitted via repeated `pair_id`/`new_value` form-field
   pairs, a hidden JSON blob assembled by `match.js`, or HTMX's native
   "include this row's inputs" pattern. Left to the `coder` pass per
   `data-dictionary.md`'s note on the merge-request shape; not a product
   ambiguity, just an implementation choice.
3. **Exact conflict-error presentation.** AC-M4-27/34 require that a
   conflict "lists the conflict" but the scope brief doesn't specify
   whether this is a flash banner, an inline per-row error, or a summary
   list. Left to the `coder` pass as a presentation detail, consistent
   with how `data-dictionary.md` describes the conflict-report shape as
   "exact rendering left to the coder pass."
4. **Default Distance function when Method changes.** When the user
   switches Method (e.g. from Fingerprint to Nearest Neighbor), which
   Distance function is pre-selected — the first option in that Method's
   list (Levenshtein / Fingerprint, by registry order), or whatever was
   last used for that Method in this session (if the user switches back
   and forth)? The scope brief doesn't address persistence-across-Method-
   switches. Recommendation: default to the first registered algorithm of
   the newly selected Method (simplest, stateless, matches "rebuilt from
   scratch" philosophy elsewhere in this milestone) unless told otherwise.
   **Flagged for the orchestrating session**, not blocking.

---

## M3 reversal — explicit callout

M4 **deliberately reverses** the M3 product decision recorded in this
project's working notes as "multi-pair cluster distance = max pairwise
distance" (`acceptance-criteria/m3-nn-algorithms-blocking.md` AC-M3-27,
OQ-M3-6). That decision applied to a *clustering* model that no longer
exists: M4 removes the `_UnionFind`-based transitive clustering for
nearest-neighbor algorithms entirely (see `frd.md` FR-4.4), so there is no
longer a "cluster" for which a maximum makes sense — every nearest-neighbor
`CandidatePair` is now a single direct pair with its own single measured
distance (AC-M4-14). This is **not** an oversight or a regression; it is
the direct mechanical consequence of the scope point "every result row is
exactly one pair of two addresses... achieved structurally without
transitive clustering."
