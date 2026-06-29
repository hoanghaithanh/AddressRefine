# Data Dictionary — AddressRefine

Status: Living document. Last revised: M3 BA pass (2026-06-29). Fields are
grouped by the module that defines them. "Shipped" = exists in code today;
"Planned/In Progress" = introduced by a documented future milestone, shape
taken from the plan and may be refined when that milestone's BA pass runs.

## `app/models/domain.py`

### `ColumnMapping` (shipped, M1)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `street_col` | `str` | must be a real CSV header at save time | Required. The only field ever fuzzy-matched. |
| `zip_col` | `str \| None` | must be a real CSV header if set | Optional; used for blocking (M3+), not fuzzy-compared. At least one of `zip_col`/`city_col` required by `MappingForm`. |
| `city_col` | `str \| None` | must be a real CSV header if set | Optional; blocking fallback when zip is blank. |
| `country_col` | `str \| None` | must be a real CSV header if set | Optional; not currently used by any algorithm or blocking rule. |

### `DatasetVersion` (shipped, M1; `created_from_merge` not yet set to `True` by any code path until M4)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `version` | `int` | starts at `1` | Not currently auto-incremented on append (M1 only ever creates version 1 on upload); M4's merge service is expected to append `version + 1`. |
| `df` | `Any` | backend-specific frame (pandas `DataFrame` in v1) | Deliberately untyped at the domain-model level to stay compute-backend-agnostic. Full snapshot per version, not a diff — acceptable at CSV scale (documented v1 tradeoff). |
| `created_from_merge` | `bool` | default `False` | `True` only for versions appended by `merge_service.apply_merge` (M4). |

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
| `candidate_pairs` | `list[CandidatePair]` | rebuilt from scratch on every `run_matching` call | Added M2. Each entry is one duplicate cluster; `pair_id` field added in M3. |

## Domain types (shipped M2 or in progress M3)

### `CandidatePair` (M2: `row_indices` + `distance`; M3 adds `pair_id`; M4 adds mutation fields)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `pair_id` | `str` | uuid4 string; unique within a single `run_matching` call | **Added in M3.** Assigned by `matching_service` at pair-construction time. Not required to be stable across reruns. Used by M4's `POST /results/pair/{id}/...` routes. |
| `row_indices` | `list[int]` | sorted; indices into the current `DatasetVersion.df` | Shipped M2. The set of rows in the cluster. |
| `distance` | `float \| None` | `None` for key-collision algorithms; numeric for NN (M3) | Shipped M2 as `None`-only. M3 populates with the **maximum** pairwise distance among all members of the cluster. Levenshtein: integer-valued float (or int). NCD: float in roughly `[0, 1]`. |
| `status` | `Literal["pending", "accepted", "rejected"]` | default `"pending"` | **Planned, M4.** Mutated only by M4's accept/reject routes. Not yet a field in code. |
| `representative_mode` | `Literal["original", "custom"]` | | **Planned, M4.** `"original"` picks one matched row's value; `"custom"` uses user-typed text. |
| `representative_row_index` | `int \| None` | required if `representative_mode == "original"` | **Planned, M4.** |
| `representative_value` | `str \| None` | required if `representative_mode == "custom"` | **Planned, M4.** |

## `app/algorithms/` types (shipped M2)

### `ParamSpec` (shipped, M2)

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Parameter key as used in `session.algorithm_params`, e.g. `"n"`, `"threshold"`. |
| `label` | `str` | Human-readable label for the form input, e.g. `"N-gram size"`, `"Threshold"`. |
| `param_type` | `type` | Python type object, e.g. `int`. Used by the router for coercion/validation. |
| `default` | `Any` | Default value. `2` for N-Gram Fingerprint `n`; `3` for Levenshtein and NCD `threshold` (M3). |

### `AlgorithmFamily` (shipped, M2)

`StrEnum` with values `KEY_COLLISION` (`"key_collision"`) and
`NEAREST_NEIGHBOR` (`"nearest_neighbor"`). Used by the registry and
results template to determine whether to show a distance sub-label.

### `AlgorithmOutput` (shipped, M2)

| Field | Type | Notes |
|---|---|---|
| `clusters` | `dict[str, list[int]]` | Populated by key-collision algorithms; keyed by the computed fingerprint key. Empty dict for NN algorithms. |
| `pairs` | `list[tuple[int, int, float]] \| None` | Populated by NN algorithms (M3): each tuple is `(row_i, row_j, distance)`. `None` for key-collision algorithms. |

## `app/algorithms/blocking.py` shapes (M3, in progress)

| Shape | Type | Notes |
|---|---|---|
| Input `rows` | `dict[int, dict[str, str]]` | Same shape as `ComputeBackend.extract_columns` output. Inner dict must have `"zip"` and `"city"` keys (empty string `""` when unmapped). |
| Block key | `str` | First 3 chars of normalized zip if non-blank; else normalized city; else `"__unblocked__"`. Normalization = strip whitespace + lowercase. |
| Output | `dict[str, list[int]]` | Maps block key → list of row indices in that block. |

### Blocking algorithm parameter — `threshold` (M3, both NN algorithms)

| Algorithm | Param name | UI type | UI range | Internal value | Notes |
|---|---|---|---|---|---|
| Levenshtein | `threshold` | `int` | `>= 0` | same as UI value | Integer edit-distance cutoff. `0` = identical strings only. Default `3`. |
| NCD / PPM | `threshold` | `int` | `1–10` | `ui_threshold / 10.0` | Displayed as integer; internally scaled to `[0.1, 1.0]`. `0` rejected. `> 10` rejected. Default `3` (internal `0.3`). |

## `app/compute/backend.py` shapes (shipped, M1)

| Shape | Type | Notes |
|---|---|---|
| Extracted row (`extract_columns` return value) | `dict[int, dict[str, str]]` | Inner dict always has keys `"street"`, `"zip"`, `"city"`, `"country"`; unmapped/missing -> `""` (never `NaN`/`None`). |
| Extracted street addresses (`extract_street_addresses` return value) | `dict[int, str]` | The only shape `app/algorithms/` is allowed to consume — never a DataFrame. |

## Config (`app/config.py`, shipped, M1)

| Field | Type | Value | Notes |
|---|---|---|---|
| `SESSION_COOKIE_NAME` | `str` | `"addressrefine_session"` | |
| `MAX_UPLOAD_BYTES` | `int` | `10 * 1024 * 1024` (10 MB) | Enforced via streaming chunked read in `routers/upload.py`, not post-hoc. |
