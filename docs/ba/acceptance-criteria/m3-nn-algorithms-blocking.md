# Acceptance Criteria — M3: Nearest-Neighbor Algorithms + Blocking

Milestone branch: `m3-nn-algorithms-blocking`
Status: Written before the `coder` pass. Source: GitHub issue #2, plan
sections "Blocking" / "Algorithm interface" / "Milestones" item 3, and
the nine resolved open questions from the M3 BA pre-authoring pass.
Each AC is in Given/When/Then form and is written to be directly
convertible to a test case by the `tester` agent. See
`traceability-matrix.md` for the expected test file/case mapping.

---

## `algorithms/blocking.py` — `compute_blocks`

### AC-M3-1 — `compute_blocks` groups rows by 3-char zip prefix

**Given** a `dict[int, dict[str, str]]` of pre-extracted rows where some
rows have a non-blank `"zip"` value,
**When** `compute_blocks(rows)` is called,
**Then** rows whose normalized zip (whitespace-stripped, lowercased)
starts with the same first 3 characters are placed in the same block,
and the block key equals those first 3 characters.

### AC-M3-2 — `compute_blocks` uses the full zip string when it is shorter than 3 chars

**Given** a row whose normalized zip value is 1 or 2 characters long
(e.g. `"AB"`),
**When** `compute_blocks(rows)` is called,
**Then** the block key for that row is the entire normalized zip string
(e.g. `"ab"`), not a truncated or padded version.

### AC-M3-3 — `compute_blocks` falls back to city when zip is blank

**Given** a `dict[int, dict[str, str]]` where some rows have a blank
`"zip"` value (`""`) and a non-blank `"city"` value,
**When** `compute_blocks(rows)` is called,
**Then** those rows are grouped by their normalized city (whitespace-stripped,
lowercased) as the block key, and are placed in a separate block from any
zip-keyed rows.

### AC-M3-4 — `compute_blocks` uses `"__unblocked__"` bucket for rows with no zip or city

**Given** a `dict[int, dict[str, str]]` where some rows have both `"zip"`
and `"city"` blank (`""`),
**When** `compute_blocks(rows)` is called,
**Then** those rows are all placed in a single block keyed
`"__unblocked__"`, and are not included in any zip- or city-keyed block.

### AC-M3-5 — Block key normalization: whitespace and case

**Given** two rows whose zip values differ only by leading/trailing
whitespace or letter case (e.g. `"012"` and `" 012"`, or `"NYC"` and
`"nyc"` as city values),
**When** `compute_blocks(rows)` is called,
**Then** both rows are placed in the same block (normalization treats
them as equivalent).

### AC-M3-6 — `compute_blocks` is a pure function: no DataFrame, no `ColumnMapping`

**Given** that `compute_blocks` is called with only a
`dict[int, dict[str, str]]` argument (no `ColumnMapping` object, no
pandas frame),
**Then** the function operates solely on the pre-extracted dict and
produces `dict[str, list[int]]` without importing or touching any
compute-backend type. (Statically verifiable: `blocking.py` must not
import `pandas`.)

---

## `algorithms/ncd.py` — `normalized_compression_distance`

### AC-M3-7 — NCD of identical strings is 0.0

**Given** two identical non-empty strings `a == b`,
**When** `normalized_compression_distance(a, b)` is called,
**Then** the result is `0.0` (or very close, within floating-point
tolerance of `1e-6`).

### AC-M3-8 — NCD of completely dissimilar strings is near 1.0

**Given** two strings with no shared content (e.g. `"aaaaaaaaaa"` vs
`"zzzzzzzzzz"` — strings that compress well individually but not
together),
**When** `normalized_compression_distance(a, b)` is called,
**Then** the result is greater than `0.5` (demonstrating the function
detects dissimilarity; exact value depends on `bz2` internals).

### AC-M3-9 — NCD is symmetric

**Given** two non-empty strings `a` and `b`,
**When** `normalized_compression_distance(a, b)` and
`normalized_compression_distance(b, a)` are both called,
**Then** both return the same value (symmetric by construction via
order-averaging: `((C(a+b)-min(Ca,Cb))/max(Ca,Cb) + (C(b+a)-min(Ca,Cb))/max(Ca,Cb)) / 2`).

### AC-M3-10 — NCD of two empty strings is 0.0

**Given** two empty strings `a = ""` and `b = ""`,
**When** `normalized_compression_distance(a, b)` is called,
**Then** the result is `0.0` (per plan: "Empty/empty → 0.0").

---

## `algorithms/nearest_neighbor.py` — `LevenshteinNNAlgorithm`

### AC-M3-11 — Levenshtein algorithm is registered with key `"levenshtein"`

**Given** `app/algorithms/registry.py`,
**When** `list_algorithms()` is called after M3,
**Then** it includes a `LevenshteinNNAlgorithm` instance with `key ==
"levenshtein"`, `label == "Levenshtein Distance"`, and `family ==
AlgorithmFamily.NEAREST_NEIGHBOR`.

### AC-M3-12 — Levenshtein `threshold` param spec

**Given** `LevenshteinNNAlgorithm.param_specs`,
**Then** it contains exactly one `ParamSpec` with `name="threshold"`,
`param_type=int`, and `default=3`.

### AC-M3-13 — Levenshtein pairs rows within threshold

**Given** a block containing two addresses with edit distance `d <=
threshold` (e.g. `"123 main st"` and `"123 main street"` with
`threshold=5`),
**When** `LevenshteinNNAlgorithm.run(addresses, blocks, {"threshold": 5})`
is called,
**Then** a pair `(row_i, row_j, d)` appears in `output.pairs` and those
rows are reachable via the union-find clustering step.

### AC-M3-14 — Levenshtein does not pair rows above threshold

**Given** two addresses with edit distance `d > threshold`,
**When** `LevenshteinNNAlgorithm.run` is called,
**Then** no pair for those two rows appears in `output.pairs`.

### AC-M3-15 — Levenshtein with `threshold=0` matches only identical strings

**Given** two rows with identical street addresses and two with
different street addresses, and `threshold=0`,
**When** `LevenshteinNNAlgorithm.run` is called,
**Then** only the identical pair produces a match; the differing pair
does not.

### AC-M3-16 — Levenshtein respects block boundaries

**Given** two addresses that are within Levenshtein threshold but in
different blocks (e.g. different zip-prefix blocks),
**When** `LevenshteinNNAlgorithm.run(addresses, blocks, params)` is called,
**Then** those two addresses do not produce a pair (cross-block
comparisons are not performed).

### AC-M3-17 — Levenshtein uses `rapidfuzz` and `score_cutoff` for efficiency

**Given** the `LevenshteinNNAlgorithm` source code,
**Then** it uses `rapidfuzz.distance.Levenshtein.distance` with the
`score_cutoff` parameter set to `threshold` (statically verifiable via
grep/code review; this is a correctness-and-performance requirement per
the plan).

---

## `algorithms/nearest_neighbor.py` — `NCDAlgorithm`

### AC-M3-18 — NCD algorithm is registered with key `"ncd"`

**Given** `app/algorithms/registry.py`,
**When** `list_algorithms()` is called after M3,
**Then** it includes an `NCDAlgorithm` instance with `key == "ncd"`,
`label == "PPM / NCD"`, and `family == AlgorithmFamily.NEAREST_NEIGHBOR`.

### AC-M3-19 — NCD `threshold` param spec

**Given** `NCDAlgorithm.param_specs`,
**Then** it contains exactly one `ParamSpec` with `name="threshold"`,
`param_type=int`, and `default=3`.

### AC-M3-20 — NCD UI threshold is scaled to internal threshold

**Given** a UI `threshold` value of `3`,
**When** `NCDAlgorithm` uses this threshold internally,
**Then** the actual NCD cutoff applied is `0.3` (i.e. `ui_threshold /
10.0`). This scaling is implemented inside `NCDAlgorithm`, documented
with a comment, and not visible to callers. (Verifiable by inspecting
`nearest_neighbor.py`; the value `0.3` should appear in a comment or
docstring as an example.)

### AC-M3-21 — NCD pairs rows within internal threshold

**Given** a block containing two addresses whose NCD score is `<=
ui_threshold / 10.0` (e.g. very similar strings with `threshold=5`,
internal cutoff `0.5`),
**When** `NCDAlgorithm.run(addresses, blocks, {"threshold": 5})` is called,
**Then** a pair `(row_i, row_j, ncd_score)` appears in `output.pairs`.

### AC-M3-22 — NCD does not pair rows above internal threshold

**Given** two very dissimilar addresses whose NCD score is `>
ui_threshold / 10.0`,
**When** `NCDAlgorithm.run` is called,
**Then** no pair for those two rows appears in `output.pairs`.

### AC-M3-23 — NCD respects block boundaries

**Given** two addresses in different blocks that would otherwise be
within NCD threshold,
**When** `NCDAlgorithm.run(addresses, blocks, params)` is called,
**Then** those two addresses do not produce a pair.

---

## `services/matching_service.py` — NN path + union-find

### AC-M3-24 — `run_matching` calls `extract_columns` for NN algorithms to obtain zip/city

**Given** a session with a nearest-neighbor algorithm selected
(Levenshtein or NCD) and a confirmed mapping,
**When** `run_matching(session)` is called,
**Then** it calls `backend.extract_columns(frame, mapping)` (which
returns `dict[int, dict[str, str]]`) to obtain per-row zip and city
values, and passes the result to `compute_blocks` — it does not attempt
to derive zip/city from the street-address string or from any new
backend method.

### AC-M3-25 — `run_matching` passes `None` for blocks to key-collision algorithms

**Given** a session with a key-collision algorithm selected (Fingerprint
or N-Gram Fingerprint),
**When** `run_matching(session)` is called,
**Then** `algorithm.run(addresses, blocks=None, params)` is called (no
`compute_blocks` invocation), consistent with M2 behavior. Key-collision
results are unaffected by this milestone's blocking logic.

### AC-M3-26 — Union-find produces one `CandidatePair` per transitive cluster

**Given** three rows A, B, C where A and B are within threshold and B
and C are within threshold (but A and C are above threshold),
**When** `run_matching` is called with a NN algorithm,
**Then** `session.candidate_pairs` contains exactly one entry with
`row_indices` including all three rows A, B, and C (not two separate
pairs).

### AC-M3-27 — `CandidatePair.distance` is the maximum pairwise distance in the cluster

**Given** a union-find cluster whose member pairs have distances
`d(A,B) = 2.0` and `d(B,C) = 4.0`,
**When** `run_matching` constructs the `CandidatePair` for this cluster,
**Then** `pair.distance == 4.0` (the maximum, i.e. most conservative,
pairwise distance).

### AC-M3-28 — Each `CandidatePair` is assigned a unique `pair_id`

**Given** a `run_matching` call that produces N candidate pairs,
**When** `session.candidate_pairs` is inspected after the call,
**Then** every `CandidatePair` has a `pair_id` attribute that is a
non-empty string, and all `pair_id` values within the list are unique
(no two pairs share the same id).

### AC-M3-29 — `run_matching` rebuilds `candidate_pairs` from scratch on every call (NN path)

**Given** a session that already has `candidate_pairs` from a previous
NN algorithm run,
**When** `run_matching` is called again (e.g. with a different threshold),
**Then** `session.candidate_pairs` is fully replaced with the new run's
output; no entries from the prior run survive.

---

## `models/domain.py` — `CandidatePair` extension

### AC-M3-30 — `CandidatePair` has a `pair_id` field

**Given** `app/models/domain.py` after M3,
**Then** `CandidatePair` has a field `pair_id: str` (populated by
`matching_service` at construction time, not defaulted to empty string
or `None`). `CandidatePair` may also have a `distance: float | None`
field as already specified; this AC only confirms `pair_id` is added.

---

## `routers/algorithm.py` — `POST /algorithm` extensions

### AC-M3-31 — `POST /algorithm` accepts `threshold` for Levenshtein with `threshold >= 0`

**Given** a submission with `algorithm_key="levenshtein"` and a
`threshold` value that is a non-negative integer (`>= 0`, e.g. `0`,
`1`, `3`, `10`),
**When** `POST /algorithm` is called,
**Then** the submission is accepted: `session.algorithm_key` is set to
`"levenshtein"`, `session.algorithm_params` contains `{"threshold":
<int>}`, `run_matching` is invoked, and the response redirects to
`/results` (HTTP 303).

### AC-M3-32 — `POST /algorithm` rejects non-integer or negative `threshold` for Levenshtein

**Given** a submission with `algorithm_key="levenshtein"` and a
`threshold` value that is non-integer (e.g. `"2.5"`, `"abc"`) or a
negative integer (e.g. `"-1"`),
**When** `POST /algorithm` is called,
**Then** the submission is rejected with HTTP 422, a flash error message
is rendered, `session.algorithm_params` is not updated, and
`run_matching` is not invoked.

### AC-M3-33 — `POST /algorithm` accepts `threshold` for NCD in range 1–10

**Given** a submission with `algorithm_key="ncd"` and a `threshold`
value that is an integer in the range `[1, 10]` (e.g. `1`, `3`, `10`),
**When** `POST /algorithm` is called,
**Then** the submission is accepted: `session.algorithm_key` is set to
`"ncd"`, `session.algorithm_params` contains `{"threshold": <int>}`,
`run_matching` is invoked, and the response redirects to `/results`.

### AC-M3-34 — `POST /algorithm` rejects `threshold=0` for NCD

**Given** a submission with `algorithm_key="ncd"` and `threshold="0"`,
**When** `POST /algorithm` is called,
**Then** the submission is rejected with HTTP 422 and a flash error
message, and `run_matching` is not invoked.

### AC-M3-35 — `POST /algorithm` rejects `threshold > 10` for NCD

**Given** a submission with `algorithm_key="ncd"` and a threshold
value `> 10` (e.g. `"11"`, `"100"`),
**When** `POST /algorithm` is called,
**Then** the submission is rejected with HTTP 422 and a flash error
message, and `run_matching` is not invoked.

### AC-M3-36 — `POST /algorithm` ignores `threshold` for key-collision algorithms

**Given** a submission with `algorithm_key="fingerprint"` (or
`"ngram_fingerprint"`) and any value for `threshold`,
**When** `POST /algorithm` is called,
**Then** `threshold` is ignored; no validation is applied to it; the
submission succeeds as long as the key-collision-specific params (e.g.
`n` for N-Gram Fingerprint) are valid.

### AC-M3-37 — `GET /algorithm` renders `threshold` input for NN algorithms

**Given** the `algorithm.html` template after M3,
**Then** a `threshold` input field is rendered (statically present in
the HTML), visible or hidden via a Jinja conditional based on the
algorithm's `family` or key. For key-collision algorithms the field is
hidden (or omitted); for NN algorithms it is shown with the current or
default value.

---

## `templates/results.html` — distance column sub-label

### AC-M3-38 — Results page shows a sub-label for the distance column scale

**Given** a session that has run the Levenshtein algorithm and produced
candidate pairs,
**When** `GET /results` is called,
**Then** the rendered page contains text indicating the distance scale
(e.g. "edit distance") near the "Distance" column header, so the user
knows the column values are integer edit distances.

### AC-M3-39 — NCD results page shows `"NCD score (0–1)"` sub-label

**Given** a session that has run the NCD algorithm and produced
candidate pairs,
**When** `GET /results` is called,
**Then** the rendered page contains text such as `"NCD score (0–1)"` or
equivalent near the "Distance" column header.

### AC-M3-40 — Key-collision results page shows no distance sub-label (or generic placeholder)

**Given** a session that has run a key-collision algorithm (Fingerprint
or N-Gram Fingerprint),
**When** `GET /results` is called,
**Then** the "Distance" column continues to show `"—"` per pair (AC-M2-21a)
and no NN-specific sub-label is rendered — no regression from M2.

---

## Backend-agnosticism (reviewer-facing, but testable)

### AC-M3-41 — No `pandas` import in `app/algorithms/blocking.py`, `ncd.py`, or `nearest_neighbor.py`

**Given** the M3 deliverable,
**Then** none of the new files `app/algorithms/blocking.py`,
`app/algorithms/ncd.py`, or `app/algorithms/nearest_neighbor.py`
import `pandas` (statically checkable — mirrors AC-M2-23 for the M2
files).

---

## Open Questions — Resolved

All nine open questions raised during the M3 BA pre-authoring pass have
been resolved. The decisions below are now encoded directly in the
acceptance criteria above.

| # | Topic | Resolution | Primary AC(s) |
|---|---|---|---|
| OQ-M3-1 | How blocking gets zip/city data | `matching_service` calls `backend.extract_columns`; result passed to `compute_blocks` | AC-M3-24 |
| OQ-M3-2 | `compute_blocks` signature (does it take `ColumnMapping`?) | Signature is `compute_blocks(rows: dict[int, dict[str, str]])` only — no `mapping` param | AC-M3-6, AC-M3-24 |
| OQ-M3-3 | Zip/city normalization for block key | Strip whitespace + lowercase before taking first 3 chars / using as city key | AC-M3-1, AC-M3-3, AC-M3-5 |
| OQ-M3-4 | `threshold` validation rules | Levenshtein: `>= 0` (int). NCD: `1–10` (int); reject 0 and > 10 with 422 + flash | AC-M3-31–AC-M3-35 |
| OQ-M3-5 | HTMX `/algorithm/params` fragment in M3? | No. Extend existing static form: add `threshold` as explicit `Form` field, shown/hidden by Jinja conditional | AC-M3-37 |
| OQ-M3-6 | Distance for union-find multi-row cluster | Store and display the **maximum** pairwise distance in `CandidatePair.distance` | AC-M3-27 |
| OQ-M3-7 | `__unblocked__` bucket UX | Implemented silently; docstring note in `blocking.py` acknowledges O(n²) degenerate case; no warning shown to user | AC-M3-4 |
| OQ-M3-8 | `pair_id` on `CandidatePair` in M3 scope? | Yes. Add `pair_id: str` (uuid4) to `CandidatePair`; assigned by `matching_service` at pair-construction time | AC-M3-28, AC-M3-30 |
| OQ-M3-9 | Distance column scale label in results | Keep "Distance" header; add per-algorithm sub-label ("edit distance" / "NCD score (0–1)"); key-collision shows no sub-label | AC-M3-38–AC-M3-40 |
