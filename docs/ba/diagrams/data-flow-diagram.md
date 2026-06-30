# Data Flow Diagram — AddressRefine

Status: Living document. Last revised: M4 BA pass (2026-06-30). `P3`/`P5`
below were merged into one combined process by M4 (was two separate
processes — algorithm selection then results review/mutation — in the
M2/M3 version of this diagram).

## Level 0 — Context

```mermaid
flowchart LR
    User["External entity: User (browser)"]
    App["Process: AddressRefine app (FastAPI)"]
    Session[("Data store: in-memory SessionStore")]

    User -- "CSV upload, mapping form, Method/Distance function/param choice, Merge? checkbox + New cell value + merge submit" --> App
    App -- "HTML pages/fragments (HTMX partial swaps), CSV download" --> User
    App -- "read/write Session (mapping, versions, candidate_pairs, algorithm_params)" --> Session
    Session -- "current session state" --> App
```

## Level 1 — Major processes

```mermaid
flowchart TD
    User["External entity: User"]
    DS_Session[("D1: SessionStore (in-memory dict[session_id, Session])")]

    P1["P1: Handle upload (routers/upload.py)"]
    P2["P2: Handle column mapping (routers/mapping.py)"]
    P3["P3: Combined algorithm selection + live results (routers/algorithm.py) - M4 merges the former P3/P5"]
    P4["P4: Run matching (services/matching_service.py)"]
    P6["P6: Apply merge (services/merge_service.py)"]
    P7["P7: Export CSV (routers/export.py)"]

    User -- "CSV file" --> P1
    P1 -- "load_csv via ComputeBackend" --> P1
    P1 -- "new DatasetVersion" --> DS_Session

    User -- "column choices" --> P2
    P2 -- "get_headers via ComputeBackend" --> DS_Session
    P2 -- "ColumnMapping" --> DS_Session

    User -- "Method + Distance function + Radius/N-Gram size (HTMX, live, no submit button)" --> P3
    P3 -- "algorithm_key + algorithm_params" --> DS_Session
    P3 --> P4

    DS_Session -- "mapping, current frame" --> P4
    P4 -- "extract_street_addresses / extract_columns via ComputeBackend" --> P4
    P4 -- "candidate_pairs (always pairwise, 2 rows each)" --> DS_Session

    DS_Session -- "candidate_pairs" --> P3
    P3 -- "renders live results-table partial" --> User

    User -- "checked pair_ids + New cell value text, Merge selected and re-cluster" --> P6
    P6 -- "conflict check (blocks on disagreement, mutates nothing)" --> P6
    P6 -- "replace_values via ComputeBackend, per checked pair" --> P6
    P6 -- "new DatasetVersion" --> DS_Session
    P6 --> P4

    DS_Session -- "current frame" --> P7
    P7 -- "to_csv_bytes via ComputeBackend" --> User
```

## Notes

- All processes that touch the dataframe go through `ComputeBackend`
  (`app/compute/backend.py`) rather than manipulating pandas directly —
  this is the seam that would let a future Spark backend be substituted.
- `P4` (matching) only ever receives `dict[int, str]` from the compute
  backend, never the frame itself — this boundary is what keeps
  `app/algorithms/` backend-agnostic.
- There is exactly one data store (`D1`, the in-memory `SessionStore`); no
  external database or third-party API is part of this system's data
  flow in v1.
- **M4 change**: the former `P5` ("Render/mutate results", with its own
  per-pair accept/reject/representative mutation path) no longer exists as
  a separate process. Live recompute (Method/Distance function/param
  change) and merge submission are now the only two write paths into `P4`,
  both routed through the single combined `P3` process — there is no
  intermediate per-pair "accepted" state stored in `D1` between them.
