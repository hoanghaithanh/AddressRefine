# Use Case Diagram — AddressRefine

Status: Living document. Last revised: M2 BA pass (2026-06-28).

> Caveat: Mermaid has no native UML use-case diagram shape (no actor/oval
> notation). The diagram below uses a `flowchart` with the actor as a node
> and use cases as rounded nodes, connected by plain edges, as an
> approximation. It should be read as "actor participates in use case", not
> as a strictly notated UML use-case diagram.

```mermaid
flowchart LR
    User(["User (data owner / operator)"])

    UC1(("Upload address CSV"))
    UC2(("Map CSV columns to address fields"))
    UC3(("Select matching algorithm and parameters"))
    UC4(("View candidate duplicate groups"))
    UC5(("Accept a candidate group"))
    UC6(("Reject a candidate group"))
    UC7(("Choose representative value for a group"))
    UC8(("Merge accepted groups"))
    UC9(("Download cleaned dataset as CSV"))

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    User --> UC7
    User --> UC8
    User --> UC9

    UC2 -. "requires" .-> UC1
    UC3 -. "requires" .-> UC2
    UC4 -. "requires" .-> UC3
    UC5 -. "requires" .-> UC4
    UC6 -. "requires" .-> UC4
    UC7 -. "requires" .-> UC5
    UC8 -. "requires" .-> UC7
    UC8 -. "triggers rerun of" .-> UC4
    UC9 -. "available any time after" .-> UC1
```

## Use case status by milestone

| Use case | Status |
|---|---|
| Upload address CSV | Shipped (M1) |
| Map CSV columns to address fields | Shipped (M1) |
| Select matching algorithm and parameters | M2 (Fingerprint/N-Gram only); M3 adds Levenshtein/PPM |
| View candidate duplicate groups | M2 (read-only); interactive accept/reject in M4 |
| Accept a candidate group | Planned (M4) |
| Reject a candidate group | Planned (M4) |
| Choose representative value for a group | Planned (M4) |
| Merge accepted groups | Planned (M4) |
| Download cleaned dataset as CSV | Planned (M5) |
