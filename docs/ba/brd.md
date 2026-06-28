# Business Requirements Document — AddressRefine

Status: Living document. Last revised: M2 BA pass (2026-06-28).

## 1. Purpose

AddressRefine lets a user upload a CSV of address records and find rows that
describe the same real-world address despite differences in formatting
(e.g. `"123-3 king st"` vs `"3 king street, unit 123"`). The user reviews
candidate matches, optionally accepts/rejects them, picks a representative
value per accepted group, merges, and the app rewrites the dataset and
reruns matching. This document captures the business problem and goals;
`frd.md` translates these goals into concrete functional behavior.

## 2. Business Problem

Address data collected from multiple sources (manual entry, imports, partner
feeds) accumulates duplicate real-world addresses written in inconsistent
formats. Naive exact-string deduplication misses these duplicates, leading
to fragmented records, wasted mailings/calls, and inaccurate counts of
distinct addresses. Manually reviewing a CSV for near-duplicates does not
scale past a few hundred rows.

## 3. Business Goals

- **G1 — Reduce manual review effort.** Surface candidate duplicate
  addresses automatically rather than requiring a human to eyeball every
  row pair.
- **G2 — Support multiple matching strategies with different
  precision/recall tradeoffs.** Different datasets call for different
  algorithms (cheap key-collision clustering vs. more expensive
  edit-distance/compression-based comparison); the user should be able to
  pick and re-pick without re-uploading.
- **G3 — Keep humans in control of merges.** No row is silently merged
  without an explicit accept + representative-value choice from the user.
- **G4 — Produce a usable cleaned-up export.** The end output is a CSV the
  user can take back into their own systems.
- **G5 — Stay operable as a lightweight, self-hosted tool.** No database,
  no auth server, no cloud dependency required for v1 — a single operator
  runs the app and works with one dataset at a time.

## 4. Scope

### In scope (v1, all milestones)

- CSV upload (single file, up to 10 MB) and column mapping (street
  required; at least one of zip/city required; country optional).
- Four matching algorithms operating on the street-address field:
  Fingerprint, N-Gram Fingerprint (key-collision family), Levenshtein
  Distance, PPM/NCD (nearest-neighbor family), each independently
  selectable with their own parameters.
- Blocking (zip-prefix / city fallback) to keep nearest-neighbor matching
  tractable on larger datasets.
- A results view where candidate matches are listed, can be accepted or
  rejected, and a representative value chosen per accepted group.
- Merge: rewriting the working dataset with representative values and
  rerunning matching on the result.
- CSV export of the current dataset state at any point.
- Continuous integration (lint + tests) from M5 onward.

### Out of scope (v1)

- Authentication/authorization, multi-tenant or multi-session concurrent
  use (single in-memory session only).
- Persistence across server restarts (no database).
- Any compute backend other than pandas (the `ComputeBackend` abstraction
  exists to make adding one easier later, but no second backend ships).
- Distributed/Spark/Microsoft Fabric execution.
- Matching on fields other than the street address (zip/city/country are
  used only for blocking, never fuzzy-compared themselves).
- Undo/redo of a merge once applied.

## 5. Stakeholders

| Stakeholder | Interest |
|---|---|
| End user / data owner | Wants accurate deduplication with minimal manual review and full control over what gets merged. |
| Project owner (solo developer, hoanghaithanh) | Wants a working, testable, incrementally-shippable tool; also the sole operator of the deployed instance in v1. |
| Future maintainer | Wants a codebase where adding an algorithm or a compute backend doesn't require touching unrelated layers (the `compute/` vs `algorithms/` seam). |

## 6. Success Criteria

- A user can go from CSV upload to a downloaded, deduplicated CSV without
  touching code or configuration.
- Each of the four algorithms produces materially different candidate sets
  on the same dataset (validating that algorithm choice is meaningful, not
  cosmetic).
- No merge happens without an explicit user accept action on that specific
  candidate group.
- The exported CSV re-imports cleanly (preserves leading-zero zips, literal
  `"NA"` tokens, row count integrity).

## 7. Assumptions and Constraints

- Single operator, single working dataset at a time (no concurrent
  multi-user session isolation beyond the cookie-keyed `SessionStore`).
- Dataset size is assumed to fit comfortably in process memory (CSV-scale,
  not big-data scale) — `DatasetVersion` stores full snapshots per version.
- The user is responsible for the legality/privacy compliance of the
  address data they upload; AddressRefine does not added any data
  governance controls in v1.

## 8. Milestone-to-Goal Mapping

| Milestone | Primary goal(s) served |
|---|---|
| M1 — Scaffold + upload + mapping | G5 (foundation), prerequisite for all others |
| M2 — Fingerprint + N-Gram Fingerprint + read-only results | G1, G2 (first two algorithms) |
| M3 — Levenshtein + NCD/PPM + blocking | G1, G2 (remaining two algorithms, made tractable via blocking) |
| M4 — Accept/reject + representative + merge/rerun | G3 |
| M5 — CSV export + CI | G4, G5 (quality gate) |
