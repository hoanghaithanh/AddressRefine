# Data Flow Diagram — AddressRefine

Status: Living document. Last revised: M2 BA pass (2026-06-28).

## Level 0 — Context

```mermaid
flowchart LR
    User["External entity: User (browser)"]
    App["Process: AddressRefine app (FastAPI)"]
    Session[("Data store: in-memory SessionStore")]

    User -- "CSV upload, mapping form, algorithm choice, accept/reject/merge actions" --> App
    App -- "HTML pages/fragments, CSV download" --> User
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
    P3["P3: Handle algorithm selection (routers/algorithm.py)"]
    P4["P4: Run matching (services/matching_service.py)"]
    P5["P5: Render/mutate results (routers/results.py)"]
    P6["P6: Apply merge (services/merge_service.py)"]
    P7["P7: Export CSV (routers/export.py)"]

    User -- "CSV file" --> P1
    P1 -- "load_csv via ComputeBackend" --> P1
    P1 -- "new DatasetVersion" --> DS_Session

    User -- "column choices" --> P2
    P2 -- "get_headers via ComputeBackend" --> DS_Session
    P2 -- "ColumnMapping" --> DS_Session

    User -- "algorithm key + params" --> P3
    P3 -- "AlgorithmParams" --> DS_Session
    P3 --> P4

    DS_Session -- "mapping, current frame" --> P4
    P4 -- "extract_street_addresses via ComputeBackend" --> P4
    P4 -- "candidate_pairs (clusters/pairs)" --> DS_Session

    DS_Session -- "candidate_pairs" --> P5
    User -- "accept/reject/representative" --> P5
    P5 -- "updated CandidatePair" --> DS_Session

    DS_Session -- "accepted pairs, current frame" --> P6
    P6 -- "replace_values via ComputeBackend" --> P6
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
