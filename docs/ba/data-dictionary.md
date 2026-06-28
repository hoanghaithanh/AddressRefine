# Data Dictionary — AddressRefine

Status: Living document. Last revised: M2 BA pass (2026-06-28). Fields are
grouped by the module that defines them. "Shipped" = exists in code today
(M1); "Planned" = introduced by a documented future milestone, shape taken
from the plan and may be refined when that milestone's BA pass runs.

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

### `Session` (shipped, M1; fields below will grow additively in M2-M4)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `session_id` | `str` | `uuid4` string | Primary key in `SessionStore._sessions`. |
| `created_at` | `datetime` | UTC, `datetime.utcnow()` default | Not currently surfaced in any UI. |
| `versions` | `list[DatasetVersion]` | append-only; last element = current | `current_df` property returns `versions[-1].df` or `None` if empty. |
| `mapping` | `ColumnMapping \| None` | `None` until `/mapping` POST succeeds | Cleared back to `None` on every new upload. |
| `original_filename` | `str \| None` | from `UploadFile.filename` | Stored for display purposes; not validated/sanitized beyond what FastAPI provides. |
| `algorithm_params` | `AlgorithmParams \| None` | **planned, M2** | Not yet a field on `Session` as of M1; M2's `coder` pass is expected to add it (plan section "Data model"). |
| `candidate_pairs` | `list[CandidatePair]` | **planned, M2** | Same as above — does not exist yet in `app/models/domain.py`. |

## Planned domain types (not yet in code — introduced by M2/M3/M4 per the plan)

### `AlgorithmParams` (planned, M2)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `algorithm_key` | `str` | must match a key in `ALGORITHM_REGISTRY` | e.g. `"fingerprint"`, `"ngram_fingerprint"` (M2); `"levenshtein"`, `"ncd"` (M3). |
| `params` | `dict[str, Any]` | shape depends on algorithm's `param_specs` | E.g. `{"n": 2}` for N-Gram Fingerprint. |

### `CandidatePair` (planned, M2 read-only rendering / M4 mutation)

| Field | Type | Format/Constraints | Notes |
|---|---|---|---|
| `pair_id` | `str` | unique within a matching run | Identifies one row in the results view; used in M4's `POST /results/pair/{id}/...` routes. |
| `cluster_id` | `str \| int` | groups one or more pairs | Both key-collision clusters and union-find-merged NN pairs are represented as clusters so they share one rendering path. |
| `row_indices` | `list[int]` | indices into the current `DatasetVersion.df` | The set of original rows considered duplicates of each other. |
| `addresses` | `list[str]` | snapshot of street values at match time | Snapshotted so the results view doesn't need to re-extract from the frame per render. |
| `distance` | `float \| int \| None` | `None` for key-collision algorithms (M2); numeric for nearest-neighbor algorithms (M3) | Levenshtein: integer edit distance. NCD: float in roughly `[0, 1]`. |
| `status` | `Literal["pending", "accepted", "rejected"]` | default `"pending"` | Mutated only by M4's accept/reject routes. |
| `representative_mode` | `Literal["original", "custom"]` | | `"original"` picks one matched row's value; `"custom"` uses user-typed text. |
| `representative_row_index` | `int \| None` | required if `representative_mode == "original"` | |
| `representative_value` | `str \| None` | required if `representative_mode == "custom"` | |

## `app/algorithms/` types (planned, M2)

### `ParamSpec` (planned, M2)

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Parameter key as used in `AlgorithmParams.params`, e.g. `"n"`, `"threshold"`. |
| `default` | `Any` | E.g. `2` for N-Gram Fingerprint's `n`; `3` for Levenshtein/PPM `threshold` (M3). |
| `type` | likely `type` or a small enum (`"int"`, `"float"`) | Exact shape is an M2 coder decision; not yet pinned down in the plan beyond "ParamSpec". |

### `AlgorithmFamily` (planned, M2)

Enum distinguishing `KEY_COLLISION` (Fingerprint, N-Gram Fingerprint) from
`NEAREST_NEIGHBOR` (Levenshtein, NCD/PPM, both M3). Used by the registry and
by the results template to decide whether to render a `distance` column.

### `AlgorithmOutput` (planned, M2)

Carries either `.clusters` (key-collision: `dict[str, list[int]]` or
similar — keyed by the computed fingerprint key) or `.pairs`
(nearest-neighbor, M3: list of `(row_i, row_j, distance)` tuples). Exact
field types to be confirmed against the M2 coder's implementation.

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
