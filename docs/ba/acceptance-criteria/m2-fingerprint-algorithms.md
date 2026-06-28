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
resulting string, deduplicated and sorted before joining. E.g. for `n=2`
on normalized `"abcab"` (after space removal), the n-gram multiset is
`{ab, bc, ca, ab}` -> deduped+sorted -> `["ab", "bc", "ca"]` -> key
`"ab bc ca"` (exact join delimiter is an implementation detail the coder
may choose, but must be deterministic and consistent for equal inputs).

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

### AC-M2-22 — `GET /results` with no algorithm run yet

Given a session with a confirmed mapping but no algorithm selection made
yet, `GET /results` shall redirect to `/algorithm` (mirroring the
upload-then-mapping and mapping-then-algorithm redirect chain).

## Backend-agnosticism (reviewer-facing, but testable)

### AC-M2-23 — No `pandas` import in `app/algorithms/`

Given the M2 deliverable, no file under `app/algorithms/` shall import
`pandas` (statically checkable via `ruff`/grep — the reviewer pass is
expected to verify this explicitly per the plan's "Reviewer checks:
... algorithms stay backend-agnostic").

## Open Questions

These are genuine ambiguities in the plan/issue text that the `coder`
should not resolve by guessing. Ranked by importance (most important
first) — see final report for the same list surfaced to the user.

1. **OQ-M2-1 (routing): What should `POST /mapping` redirect to once M2
   ships?** `app/routers/mapping.py` currently has a code comment stating
   the redirect target changes from `/mapping` to `/algorithm` "once
   Milestone 2 adds the algorithm-selection step." Neither the plan nor
   issue #1 explicitly lists changing `mapping.py`'s redirect as M2 scope
   (issue #1's file list only mentions `algorithm.py`/`results.py` as new
   files). Should M2 change this existing redirect, or is that deferred
   to whichever milestone is judged to "complete" the navigation chain?
   Recommendation: change it now, since otherwise `/algorithm` is
   unreachable from the normal flow and M2 ships an unreachable feature.

2. **OQ-M2-2 (param input validation): What happens if `n` is submitted
   as 0, negative, or non-integer to `POST /algorithm`?** Neither the
   plan nor the issue specifies bounds for `n`. A value of `0` or
   negative would make "all character n-grams" undefined/empty.
   Recommendation: validate `n >= 1` (matching `ParamSpec`-declared type
   `int`), reject otherwise with a 422 + flash error, analogous to
   M1's mapping-validation pattern. Needs explicit confirmation since
   it's user-facing validation behavior, not just an internal detail.

3. **OQ-M2-3 (results grouping for key-collision results when nothing
   matches): What does `GET /results` show when the algorithm produces
   zero multi-row clusters (e.g. dataset has no duplicates at all)?**
   Neither the plan nor issue says whether this is an empty table, a
   specific "no duplicates found" message, or something else.
   Recommendation: render an explicit empty-state message rather than a
   bare empty table, but needs UX confirmation.

4. **OQ-M2-4 (n-gram key delimiter / exact key format): The plan
   describes the n-gram fingerprint key only at the algorithm level
   ("dedupe -> sort -> join") without specifying the join delimiter or
   whether it must be stable/human-readable.** This doesn't affect
   correctness (any deterministic delimiter works, AC-M2-12 above is
   delimiter-agnostic) but does affect whether the results UI can ever
   meaningfully display the "key" itself for debugging. Low-importance —
   flagging in case the coder wants a steer rather than picking
   arbitrarily.

5. **OQ-M2-5 (distance column in M2's results table): Issue #1 doesn't
   restate whether `_results_table.html`/`_pair_row.html` (per the plan's
   project structure section) should already include a `distance` column
   that is simply blank/`None` for M2's key-collision-only algorithms, or
   whether that column should not exist in markup until M3 introduces
   nearest-neighbor algorithms that populate it.** Recommendation: include
   the column now (rendering blank for key-collision rows) so M3 doesn't
   need a template restructure, but this is a coder-level UI decision
   worth a quick confirmation since it touches shared partial templates.
