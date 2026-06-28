# Business Process Models — AddressRefine

Status: Living document. Last revised: M2 BA pass (2026-06-28).

## As-Is: Manual address deduplication (before AddressRefine)

```mermaid
flowchart TD
    A[Export/collect address list as spreadsheet] --> B[Sort or eyeball rows manually]
    B --> C{Looks like a duplicate?}
    C -- "Yes, obviously" --> D[Manually edit/delete row]
    C -- "Maybe, unsure" --> E[Skip - too time consuming to verify]
    C -- "No" --> F[Leave row as-is]
    D --> G[Re-save spreadsheet]
    E --> G
    F --> G
    G --> H[Duplicates with formatting differences remain undetected]
```

Key pain points this process has: no systematic similarity comparison, no
record of why a row was judged duplicate/not, doesn't scale past a few
hundred rows, easy to introduce data-loss by editing the wrong row.

## To-Be: AddressRefine workflow

```mermaid
flowchart TD
    A[User uploads CSV] --> B{CSV valid and non-empty?}
    B -- No --> A2[Show upload error, stay on upload page]
    B -- Yes --> C[User maps columns: street required, zip/city/country optional]
    C --> D{Mapping valid - all columns real headers, zip or city present?}
    D -- No --> C
    D -- Yes --> E[User selects matching algorithm and parameters]
    E --> F[System runs matching: key-collision or nearest-neighbor plus blocking]
    F --> G[System renders candidate match groups in results view]
    G --> H[User accepts or rejects each candidate group]
    H --> I[User picks a representative value per accepted group]
    I --> J[User triggers merge]
    J --> K[System rewrites dataset rows, appends new DatasetVersion]
    K --> F
    G --> L[User downloads current dataset as CSV]
    K --> L
```

Note: the loop from `K` back to `F` is deliberate — `merge_service.apply_merge`
reruns matching immediately after a merge so the results view always reflects
current data, using whatever algorithm/params are currently selected.

## Sequence: end-to-end happy path (target state, all milestones)

```mermaid
sequenceDiagram
    actor User
    participant Upload as upload router
    participant Mapping as mapping router
    participant Algorithm as algorithm router
    participant Matching as matching_service
    participant Results as results router
    participant Merge as merge_service
    participant Export as export router
    participant Backend as ComputeBackend

    User->>Upload: POST /upload (CSV file)
    Upload->>Backend: load_csv(bytes)
    Backend-->>Upload: frame
    Upload-->>User: 303 redirect to /mapping

    User->>Mapping: POST /mapping (street/zip/city/country)
    Mapping->>Backend: get_headers(frame)
    Mapping-->>User: 303 redirect (to /algorithm from M2 onward)

    User->>Algorithm: POST /algorithm (algorithm_key, params)
    Algorithm->>Matching: run_matching(session, backend)
    Matching->>Backend: extract_street_addresses(frame, mapping)
    Matching-->>Algorithm: candidate_pairs populated on session
    Algorithm-->>User: render results

    User->>Results: POST /results/pair/{id}/accept
    Results-->>User: updated row fragment (HTMX)

    User->>Merge: POST /merge
    Merge->>Backend: replace_values(frame, street_col, row_indices, representative)
    Merge->>Matching: run_matching(session, backend)
    Merge-->>User: refreshed results table

    User->>Export: GET /export.csv
    Export->>Backend: to_csv_bytes(frame)
    Export-->>User: CSV download
```
