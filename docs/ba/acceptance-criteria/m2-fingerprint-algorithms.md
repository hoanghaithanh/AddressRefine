# Acceptance Criteria — M2: Fingerprint + N-Gram Fingerprint Algorithms + Read-Only Results

Status: Forward-looking, written before the `coder` pass starts. Source:
GitHub issue #1, plan section "Algorithm interface" / "Milestones" item 2,
and `CLAUDE.md`'s `compute/` vs `algorithms/` seam convention. Each AC below
is written to be directly convertible into a test case by the `tester`
agent; see `traceability-matrix.md` for the expected test file/case
mapping.

## `algorithms/base.py` — interface

### AC-M2-1 — `MatchingAlgorithm` ABC shape

Given the `MatchingAlgorithm` abstract base class, it shall declare class
variables `key: str`, `label: str`, `family: AlgorithmFamily`, and
`param_specs: list[ParamSpec] = []` (default empty list for algorithms
with no parameters, e.g. plain Fingerprint), and an abstract method
`run(self, addresses: dict[int, str], blocks: dict[str, list[int]] | None,
params: dict[str, Any]) -> AlgorithmOutput`.

### AC-M2-2 — `AlgorithmOutput` carries clusters for key-collision algorithms

Given a key-collision algorithm's `run()` result, `AlgorithmOutput.clusters`
shall be populated (a mapping from a cluster key to the list of row indices
sharing that key) and `.pairs` shall be `None` or empty for this family.

### AC-M2-3 — Registry exposes both M2 algorithms

Given `app/algorithms/registry.py`, `list_algorithms()` shall return both
`FingerprintAlgorithm` (key `"fingerprint"`) and `NGramFingerprintAlgorithm`
(key `"ngram_fingerprint"`), and `get_algorithm("fingerprint")` /
`get_algorithm("ngram_fingerprint")` shall each return the correct class/
instance.

## `algorithms/fingerprint.py` — `FingerprintAlgorithm`

### AC-M2-4 — Normalization: case and punctuation insensitivity

Given two addresses `"123 Main St."` and `"123 MAIN ST"`, when both are run
through `FingerprintAlgorithm`, they shall produce the same fingerprint key
(lowercinsensitive, punctuation stripped).

### AC-M2-5 — Normalization: whitespace collapsing

Given an address with multiple consecutive spaces, e.g. `"123  Main   St"`,
its fingerprint key shall equal that of `"123 Main St"` (single-spaced).

### AC-M2-6 — Token order does not affect the key

Given `"3 King St Unit 123"` and `"Unit 123 3 King St"` (same tokens,
different order), they shall produce the same fingerprint key (tokens are
deduplicated and sorted before joining).

### AC-M2-7 — Duplicate tokens are deduplicated

Given an address containing a repeated word, e.g. `"the the corner store"`,
the fingerprint key shall contain `"the"` only once (post-dedupe).

### AC-M2-8 — Two non-matching addresses produce different keys and are not clustered

Given `"123 Main St"` and `"456 Oak Ave"`, their fingerprint keys shall
differ, and they shall not appear in the same cluster.

### AC-M2-9 — Blank/whitespace-only address is excluded from clustering

Given a row whose extracted street address is `""` or all-whitespace, that
row shall not appear in any cluster produced by `FingerprintAlgorithm` (per
the plan: "Blank -> excluded from clustering").

### AC-M2-10 — Singleton keys do not produce a cluster/candidate pair

Given a row whose fingerprint key matches no other row, `matching_service`
shall not create a `CandidatePair`/cluster entry for it (a cluster needs
>= 2 row indices to be surfaced as a candidate).

## `algorithms/fingerprint.py` — `NGramFingerprintAlgorithm`

### AC-M2-11 — Default `n` is 2

Given no explicit `n` param, `NGramFingerprintAlgorithm`'s `param_specs`
shall declare a default of `2` for `n`, and calling `run()` with an empty
`params` dict shall behave identically to passing `{"n": 2}`.

### AC-M2-12 — N-gram key construction

Given normalization (lowercase, strip punctuation) followed by space
removal, the key shall be built from all character n-grams of the
resulting string, deduplicated and sorted, then joined with a hyphen
(`"-"`) delimiter. E.g. for `n=2` on normalized `"abcab"` (after space
removal), the n-gram multiset is `{ab, bc, ca, ab}` -> deduped+sorted ->
`["ab", "bc", "ca"]` -> key `"ab-bc-ca"`. The delimiter is fixed
(resolved, no longer implementation-defined) so fingerprint keys are
comparable/loggable across runs and across any future debugging surface
that displays them.

### AC-M2-13 — Strings shorter than `n` are excluded from clustering

Given a normalized, space-removed address shorter than `n` characters
(e.g. a single-character street value with `n=2`), that row shall be
excluded from clustering (per the plan: "Shorter than n -> excluded"),
mirroring the blank-address exclusion behavior of plain Fingerprint.

### AC-M2-14 — Different `n` values can produce different cluster assignments

Given the same address set run with `n=2` vs `n=3`, the resulting clusters
are not required to be identical — this is a property test confirming the
`n` parameter is actually wired through to the algorithm, not a specific
expected clustering.

## `services/matching_service.py`

### AC-M2-15 — `run_matching` extracts addresses via the compute backend, not directly

Given a `Session` with a `mapping` and a current dataframe, `run_matching`
shall obtain addresses via `backend.extract_street_addresses(frame,
mapping)` — never by importing pandas or touching `frame` directly in
`matching_service` or in any `algorithms/` module.

### AC-M2-16 — `run_matching` rebuilds `candidate_pairs` from scratch

Given a `Session` that already has `candidate_pairs` populated from a
previous run, calling `run_matching` again shall replace
`session.candidate_pairs` entirely (no leftover entries from the prior
run, no duplicate entries for unchanged clusters).

### AC-M2-17 — Each multi-row cluster becomes exactly one candidate-pair/group entry

Given an algorithm result with a cluster of 3 row indices, `run_matching`
shall produce exactly one entry in `session.candidate_pairs` representing
all 3 rows together (not 3 separate pairwise entries) — consistent with
the plan's clusters-not-raw-pairs rendering model.

## Routers

### AC-M2-18 — `GET /algorithm` renders algorithm choices

Given a session with a confirmed mapping, `GET /algorithm` shall return
HTTP 200 and list both `"fingerprint"` and `"ngram_fingerprint"` as
selectable options.

### AC-M2-19 — `GET /algorithm` without a confirmed mapping redirects

Given a session with no `session.mapping` set yet, `GET /algorithm` shall
redirect (303) back to `/mapping`, consistent with M1's pattern of
redirecting `/mapping` back to `/` when there's no dataset.

### AC-M2-20 — `POST /algorithm` persists the choice and triggers matching

Given a valid algorithm key and params submitted to `POST /algorithm`,
the session's algorithm selection shall be persisted and `run_matching`
shall be invoked before the response is returned (i.e. `/results`
immediately reflects the new selection without a separate trigger step).

### AC-M2-21 — `GET /results` renders candidate groups read-only

Given `session.candidate_pairs` is populated, `GET /results` shall return
HTTP 200 and render each group's row addresses. Accept/Reject controls may
be present in the markup (per the issue: "checkboxes inert") but there
shall be no working `POST` handler under `/results/*` in M2 — any such
request shall 404 or otherwise have no effect on `candidate_pairs`.

### AC-M2-21a — Results table includes a `distance` column, blank for M2's key-collision algorithms

Given `_results_table.html`/`_pair_row.html` already render from
`CandidatePair`, whose `distance` field is `None` for key-collision
algorithms per the plan's data model (`"distance" (None for
key-collision)`), the M2 results table shall include a `distance` column
that renders blank (or a placeholder such as `"—"`) whenever
`pair.distance is None`, rather than omitting the column from markup
entirely (resolves OQ-M2-5). Rationale for forcing this in now: the field
already exists in `CandidatePair`'s specified shape with a `None`
default, so rendering it conditionally (`{% if pair.distance is not none
%}...{% endif %}`) is a one-line template conditional, not a data-shape
or plumbing change — the "no awkward complication" bar from the
coordinator's resolution is met. If the M2 coder finds this requires
more than that (e.g. the partial templates don't yet exist in a shape
where `pair.distance` is cheaply accessible), they should flag it back
rather than force a workaround, per the coordinator's original
condition.

### AC-M2-22 — `GET /results` with no algorithm run yet

Given a session with a confirmed mapping but no algorithm selection made
yet, `GET /results` shall redirect to `/algorithm` (mirroring the
upload-then-mapping and mapping-then-algorithm redirect chain).

### AC-M2-24 — `POST /mapping` redirects to `/algorithm`, not `/mapping`

Given a valid mapping submission, `POST /mapping` shall redirect (303) to
`/algorithm` rather than back to `/mapping`. This changes M1's existing
redirect target as part of M2 scope (resolves OQ-M2-1): `/algorithm`
would otherwise be unreachable through the normal navigation flow once
it exists. `app/routers/mapping.py`'s existing code comment already
anticipated this change.

### AC-M2-25 — `POST /algorithm` rejects invalid `n` for N-Gram Fingerprint

Given a submission to `POST /algorithm` with `algorithm_key=
"ngram_fingerprint"` and an `n` value that is not a positive integer
(`n <= 0`, e.g. `0` or `-1`, or a non-integer value), the system shall
reject the submission with HTTP 422 and a flash error message, and shall
**not** persist the invalid params onto `session.algorithm_params` nor
invoke `run_matching`. Valid integers `n >= 1` shall be accepted
(resolves OQ-M2-2). This mirrors the validation pattern already
established in `app/routers/mapping.py` (re-render with a 422 + flash
message rather than a generic 500/stack trace).

### AC-M2-26 — `GET /results` shows an actionable empty state when no clusters are found

Given an algorithm run that produces zero multi-row clusters (no
candidate pairs at all), `GET /results` shall render an explicit message
that both states no candidate duplicates were found **and** suggests a
concrete next action — trying a different algorithm or adjusting the
current algorithm's parameters (e.g. "No candidate duplicates found with
the current algorithm and settings. Try a different algorithm, or adjust
its parameters, from the Algorithm step.") — rather than a bare empty
table or a generic "no duplicates" message with no follow-up action
(resolves OQ-M2-3). This empty state shall be distinguishable in markup
from AC-M2-21's populated-results case (e.g. a dedicated element/class)
so the `tester` agent can assert on it directly rather than inferring it
from an absent table.

## Backend-agnosticism (reviewer-facing, but testable)

### AC-M2-23 — No `pandas` import in `app/algorithms/`

Given the M2 deliverable, no file under `app/algorithms/` shall import
`pandas` (statically checkable via `ruff`/grep — the reviewer pass is
expected to verify this explicitly per the plan's "Reviewer checks:
... algorithms stay backend-agnostic").

## Open Questions — Resolved

All five open questions originally raised during this BA pass have been
resolved (decisions relayed by the orchestrating session). Each is now a
concrete, testable acceptance criterion above rather than an open
ambiguity. No unresolved open questions remain for M2 as of this update.

| # | Topic | Resolution | AC |
|---|---|---|---|
| OQ-M2-1 | `POST /mapping` redirect target | Changes to `/algorithm` as part of M2 scope | AC-M2-24 |
| OQ-M2-2 | `n` parameter validation | Validate `n >= 1`; reject with 422 + flash error otherwise | AC-M2-25 |
| OQ-M2-3 | Empty-results UX | Explicit message that both states no matches were found and nudges the user toward trying a different algorithm/param | AC-M2-26 |
| OQ-M2-4 | N-gram key join delimiter | Fixed as hyphen (`"-"`) | AC-M2-12 (updated) |
| OQ-M2-5 | `distance` column in M2's results table | Include it now, rendered blank for key-collision algorithms; judged not to introduce awkward plumbing since `CandidatePair.distance` already defaults to `None` in the specified data model | AC-M2-21a |
