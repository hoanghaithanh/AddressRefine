# Data Dictionary — AddressRefine

Status: Living document. Last revised: M4 BA pass (2026-06-30). Fields are
grouped by the module that defines them. "Shipped" = exists in code today;
"Planned/In Progress" = introduced by a documented future milestone, shape
taken from the plan and may be refined when that milestone's BA pass runs.

**M4 scope reversal note**: the M4 BA pass for the new merge-review design
(replacing the originally-planned accept/reject/pending-status model) drops
the previously "Planned, M4" fields `status`, `representative_mode`,
`representative_row_index`, `representative_value` on `CandidatePair`
entirely — see that entry below. There is no per-pair persisted status of
any kind in the shipped M4 design; the live results table is always
rebuilt fresh from `run_matching`, and the only mutating user action is the
batch "Merge selected & re-cluster" submit (see `frd.md` FR-6).

## `app/models/domain.py`

### `ColumnMapping` (shipped, M1)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `street_col` | `str` | must be a real CSV header at save time | Required. The only field ever fuzzy-matched. |
| `zip_col` | `str \| None` | must be a real CSV header if set | Optional; used for blocking (M3+), not fuzzy-compared. At least one of `zip_col`/`city_col` required by `MappingForm`. |
| `city_col` | `str \| None` | must be a real CSV header if set | Optional; blocking fallback when zip is blank. |
| `country_col` | `str \| None` | must be a real CSV header if set | Optional; not currently used by any algorithm or blocking rule. |

### `DatasetVersion` (shipped, M1; `created_from_merge` set to `True` by `merge_service.apply_merge` from M4 onward)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `version` | `int` | starts at `1` | Not currently auto-incremented on append (M1 only ever creates version 1 on upload); M4's `merge_service.apply_merge` appends `version = previous_version + 1` on every successful (non-conflicting, >= 1 row checked) merge. |
| `df` | `Any` | backend-specific frame (pandas `DataFrame` in v1) | Deliberately untyped at the domain-model level to stay compute-backend-agnostic. Full snapshot per version, not a diff — acceptable at CSV scale (documented v1 tradeoff). |
| `created_from_merge` | `bool` | default `False` | `True` only for versions appended by `merge_service.apply_merge` (M4). A merge with zero checked rows is a no-op (frd.md FR-6.5) and does **not** append a version; a merge that detects a conflict (FR-6.3) is blocked and also does not append a version. |

### `Session` (shipped, M1; `algorithm_key` + `algorithm_params` + `candidate_pairs` added M2)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `session_id` | `str` | `uuid4` string | Primary key in `SessionStore._sessions`. |
| `created_at` | `datetime` | UTC, `datetime.utcnow()` default | Not currently surfaced in any UI. |
| `versions` | `list[DatasetVersion]` | append-only; last element = current | `current_df` property returns `versions[-1].df` or `None` if empty. |
| `mapping` | `ColumnMapping \| None` | `None` until `/mapping` POST succeeds | Cleared back to `None` on every new upload. |
| `original_filename` | `str \| None` | from `UploadFile.filename` | Stored for display purposes; not validated/sanitized beyond what FastAPI provides. |
| `algorithm_key` | `str \| None` | must match a key in `ALGORITHM_REGISTRY` if set | Added M2. `None` until `POST /algorithm` succeeds. |
| `algorithm_params` | `dict[str, Any]` | shape depends on algorithm's `param_specs` | Added M2. E.g. `{"n": 2}` for N-Gram Fingerprint; `{"threshold": 3}` for Levenshtein/NCD (M3). |
| `candidate_pairs` | `list[CandidatePair]` | rebuilt from scratch on every `run_matching` call | Added M2. M2/M3: each entry was one duplicate cluster (possibly >2 rows). **As of M4: each entry is exactly one pair of 2 rows** — clusters are exploded pairwise (key-collision) or never transitively formed in the first place (nearest-neighbor); see the `CandidatePair` entry below. `pair_id` field added in M3. |

## Domain types (shipped M2/M3; M4 changes the shape and meaning of `CandidatePair`)

### `CandidatePair` (M2: `row_indices` + `distance`; M3 adds `pair_id`; M4
fixes `row_indices` to always be length 2 and drops the previously-planned
mutation fields)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `pair_id` | `str` | uuid4 string; unique within a single `run_matching` call | Added in M3. Assigned by `matching_service` at pair-construction time. Not required to be stable across reruns. As of M4, used only to correlate a checked row's "Merge?" state + edited "New cell value" with its pair when submitting `POST /merge` — there is no `POST /results/pair/{id}/...` mutation route (that plan is dropped, see below). |
| `row_indices` | `list[int]` | sorted; **always exactly 2 elements as of M4** (`len(row_indices) == 2`); indices into the current `DatasetVersion.df` | M2/M3: variable-length cluster (could be >= 2 rows via key-collision grouping or NN union-find). **M4 (breaking change): always a pair of exactly 2 row indices.** Key-collision clusters of size N now explode into `C(N, 2)` separate `CandidatePair`s (one per pairwise combination) instead of one N-member entry. Nearest-neighbor algorithms already only return pairs (never transitively clustered, per M4's removal of `_UnionFind` — see `frd.md` FR-4.4), so each returned pair maps 1:1 onto one `CandidatePair`. |
| `distance` | `float \| None` | `None` for key-collision-family pairs; numeric for NN-family pairs | M2: `None`-only. M3: populated with the maximum pairwise distance among cluster members (a meaning that no longer applies as of M4, since clusters no longer exist). **M4: populated with the single pairwise distance for that exact pair**, as returned directly by the NN algorithm's `AlgorithmOutput.pairs` tuple — not a maximum/aggregate of anything. Still `None` for fingerprint-family pairs (same-key equality is the match condition; no distance check applies, so there is no numeric value to show — the UI omits the Distance column/cell for these rows entirely, not just renders "—" as in M2/M3). |

**Dropped in M4 (were "Planned, M4" in the pre-M4 data dictionary; never
implemented in code; removed from scope entirely by the M4 redesign, not
deferred):**

| Field | Why dropped |
|---|---|
| `status: Literal["pending", "accepted", "rejected"]` | M4's redesigned UX has no per-pair accept/reject/pending state machine at all. The live results table has no concept of "dismissing" or "rejecting" a pair — a pair a user doesn't want merged is simply left with its "Merge?" checkbox unchecked, and no state persists across a recompute regardless. |
| `representative_mode: Literal["original", "custom"]` | Superseded by the single free-text "New cell value" input (frd.md FR-5.3), which is always directly editable — there is no separate "pick original vs. type custom" mode toggle. |
| `representative_row_index: int \| None` | Superseded by "New cell value"; clicking an address (frd.md FR-5.5) sets the text field directly rather than recording which original row was chosen. |
| `representative_value: str \| None` | Superseded by "New cell value" — same field, renamed and unconditionally present (not gated behind a `representative_mode == "custom"` check). |

**New in M4 (request/response shapes, not domain dataclass fields — these
are the per-row inputs `POST /merge` reads from the submitted form, not
persisted on `Session` or `CandidatePair`):**

| Shape | Type | Notes |
|---|---|---|
| Merge request row | `{pair_id: str, new_value: str}` | One entry per **checked** row in the live table at submit time. Unchecked rows are not included in the submission at all (no `checked: bool` flag needed — presence in the submitted set *is* the checked signal). The exact wire format (e.g. parallel form arrays vs. a JSON body) is left to the `coder` pass; this is the logical shape `merge_service.apply_merge` needs, not a binding API contract. |
| Conflict report (on blocked merge) | `dict[int, list[str]]` (row_index -> list of distinct conflicting target values) or equivalent | Returned only on the conflict-blocked path (frd.md FR-6.3). Exact rendering (flash message vs. structured list) is left to the `coder` pass. |

## `app/algorithms/` types (shipped M2)

### `ParamSpec` (shipped, M2; `label` text updated M4 for Levenshtein/NCD/N-Gram)

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Parameter key as used in `session.algorithm_params`, e.g. `"n"`, `"threshold"`. Unchanged by M4 — only `label` (the displayed text) changes. |
| `label` | `str` | Human-readable label for the form input. **M4 relabeling**: Levenshtein's and NCD's `threshold` param spec label changes to `"Radius"` (was `"Max edit distance"` / `"Similarity threshold (1–10)"`); N-Gram Fingerprint's `n` param spec label changes to `"N-Gram size"` (was `"N-gram size"` — capitalization also normalized). The underlying `name` (`"threshold"` / `"n"`), `param_type`, valid range, and default are unchanged — this is a display-only rename per `frd.md` FR-3.3. |
| `param_type` | `type` | Python type object, e.g. `int`. Used by the router for coercion/validation. |
| `default` | `Any` | Default value. `2` for N-Gram Fingerprint `n`; `3` for Levenshtein and NCD `threshold` (M3). Unchanged by M4. |

### `AlgorithmFamily` (shipped, M2)

`StrEnum` with values `KEY_COLLISION` (`"key_collision"`) and
`NEAREST_NEIGHBOR` (`"nearest_neighbor"`). Used by the registry and, as of
M4, the combined algorithm/results page to (a) filter the Distance function
dropdown's options by the selected Method (`frd.md` FR-3.2) and (b)
determine whether to show the Distance column for a given pair's row.

### `AlgorithmOutput` (shipped, M2)

| Field | Type | Notes |
|---|---|---|
| `clusters` | `dict[str, list[int]]` | Populated by key-collision algorithms; keyed by the computed fingerprint key. Empty dict for NN algorithms. As of M4, `matching_service` explodes every cluster of size N into `C(N, 2)` pairwise `CandidatePair`s rather than emitting one N-member `CandidatePair` — this happens in `matching_service`, not in `AlgorithmOutput` itself, so the algorithm-level shape of `clusters` is unchanged. |
| `pairs` | `list[tuple[int, int, float]] \| None` | Populated by NN algorithms (M3): each tuple is `(row_i, row_j, distance)`. `None` for key-collision algorithms. As of M4, `matching_service` maps each tuple directly to one `CandidatePair` (no union-find step) — see `frd.md` FR-4.4. |

## `app/algorithms/blocking.py` shapes (M3, shipped)

| Shape | Type | Notes |
|---|---|---|
| Input `rows` | `dict[int, dict[str, str]]` | Same shape as `ComputeBackend.extract_columns` output. Inner dict must have `"zip"` and `"city"` keys (empty string `""` when unmapped). |
| Block key | `str` | First 3 chars of normalized zip if non-blank; else normalized city; else `"__unblocked__"`. Normalization = strip whitespace + lowercase. |
| Output | `dict[str, list[int]]` | Maps block key → list of row indices in that block. |

### Blocking algorithm parameter — `threshold` (M3, both NN algorithms; M4 relabels the displayed field to "Radius")

| Algorithm | Param name | Displayed label | UI type | UI range | Internal value | Notes |
|---|---|---|---|---|---|---|
| Levenshtein | `threshold` | `"Radius"` (was `"Max edit distance"`) | `int` | `>= 0` | same as UI value | Integer edit-distance cutoff. `0` = identical strings only. Default `3`. Param name/semantics/range unchanged by M4 — only the label text changes. |
| NCD / PPM | `threshold` | `"Radius"` (was `"Similarity threshold (1–10)"`) | `int` | `1–10` | `ui_threshold / 10.0` | Displayed as integer; internally scaled to `[0.1, 1.0]`. `0` rejected. `> 10` rejected. Default `3` (internal `0.3`). Param name/semantics/range unchanged by M4 — only the label text changes. |

## `app/compute/backend.py` shapes (shipped, M1; `replace_values` implemented M4)

| Shape | Type | Notes |
|---|---|---|
| Extracted row (`extract_columns` return value) | `dict[int, dict[str, str]]` | Inner dict always has keys `"street"`, `"zip"`, `"city"`, `"country"`; unmapped/missing -> `""` (never `NaN`/`None`). |
| Extracted street addresses (`extract_street_addresses` return value) | `dict[int, str]` | The only shape `app/algorithms/` is allowed to consume — never a DataFrame. |
| `replace_values(frame, street_col, row_indices, new_value)` return value | same backend-specific frame type as `frame` (pandas `DataFrame` in v1) | **M1**: stub, `raise NotImplementedError`. **M4**: real implementation — sets `street_col` to `new_value` at each index in `row_indices` and returns the mutated/rewritten frame. Per `frd.md` FR-6.2, `merge_service.apply_merge` calls this once per checked pair with `row_indices` = that pair's exact 2 row indices, and is idempotent if a target row's value already equals `new_value`. Whether the implementation mutates `frame` in place or returns a copy is an implementation detail left to the `coder` pass (not asserted here), as long as the caller-visible contract — "the returned frame has `new_value` at those indices" — holds. |

## Config (`app/config.py`, shipped, M1)

| Field | Type | Value | Notes |
|---|---|---|---|
| `SESSION_COOKIE_NAME` | `str` | `"addressrefine_session"` | |
| `MAX_UPLOAD_BYTES` | `int` | `10 * 1024 * 1024` (10 MB) | Enforced via streaming chunked read in `routers/upload.py`, not post-hoc. |
