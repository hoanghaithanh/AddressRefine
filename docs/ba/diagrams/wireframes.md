# Wireframes — AddressRefine

Status: Living document. Last revised: M4 BA pass (2026-06-30). ASCII-art
approximations of the server-rendered Jinja2 templates under
`app/templates/`. All pages extend `base.html`'s header + step indicator.

**Visual styling note (chore/frontend-redesign-openrefine, 2026-06-29):** the
ASCII layouts below describe *structure* only and are unchanged by the
OpenRefine-visual-language chore (issue #10) — that chore is explicitly
scoped as "visual only, current structure" (see
`docs/ba/acceptance-criteria/chore-frontend-redesign.md`). For colors,
typography, spacing, table/button styling, and the control-row/control-group
form layout pattern now applied within these same box layouts, see
`docs/design/ui-design-spec.md`.

**M4 structural note:** Screens 3 ("Algorithm Selection") and 4
("Results") described in the M2/M3 version of this file are merged into one
combined screen as of M4, modeled on
`docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`. The
step indicator collapses from 4 steps to 3 (`[1. Upload] [2. Mapping]
[3. Algorithm & Results]`) — see Screen 3 below for the new layout, which
replaces both former Screen 3 and Screen 4.

## Shared header / step indicator (`base.html`)

```
+--------------------------------------------------------------------+
| AddressRefine                                                       |
| [1. Upload] [2. Mapping] [3. Algorithm & Results]                   |
|  (current step highlighted via "current" CSS class)                 |
+--------------------------------------------------------------------+
| <flash message area, if any, from partials/_flash.html>             |
|                                                                       |
|  ... page content (block content) ...                               |
+--------------------------------------------------------------------+
```

## Screen 1 — Upload (`upload.html`, shipped M1)

```
+--------------------------------------------------------------------+
| Upload your address CSV                                             |
|                                                                       |
| Choose a CSV file containing the addresses you want to de-duplicate. |
|                                                                       |
|  [ Choose File... ]   (input type=file, accept=.csv, required)       |
|                                                                       |
|  [ Upload ]                                                          |
+--------------------------------------------------------------------+
```

## Screen 2 — Column Mapping (`mapping.html`, shipped M1)

```
+--------------------------------------------------------------------+
| Map your columns                                                     |
| Street is required; at least one of Zip or City is also required.   |
|                                                                       |
|  Street (required)   [ StreetAddress         v ]                    |
|  Zip                  [ ZipCode               v ]                    |
|  City                 [ City                  v ]                    |
|  Country              [ Country               v ]                    |
|                                                                       |
|  [ Save mapping ]                                                    |
+--------------------------------------------------------------------+
```

Each dropdown lists every real CSV header plus a placeholder
(`-- choose --` for street, `-- none --` for the optional three). Selected
option reflects either the user's saved `session.mapping` or, if none yet,
a best-guess match on header name substrings.

## Screen 3 (M2/M3 history) — Algorithm Selection (`algorithm.html`, shipped M2/M3, superseded M4)

```
+--------------------------------------------------------------------+
| Choose a matching algorithm                                          |
|                                                                       |
|  Algorithm   ( ) Fingerprint                                         |
|              (o) N-Gram Fingerprint                                  |
|                                                                       |
|  -- params for selected algorithm --                                  |
|  +----------------------------------------------------------------+ |
|  | n (n-gram size)   [ 2 ]                                          | |
|  +----------------------------------------------------------------+ |
|                                                                       |
|  [ Run matching ]                                                    |
+--------------------------------------------------------------------+
```

M2/M3 history only: this single-select Algorithm field plus a flat
`threshold` field, ending in a `POST /algorithm` form submit that redirects
to a separate `/results` page, is **replaced by Screen 3 below as of M4.**

## Screen 3 — Algorithm Selection & Live Results (M4: `algorithm.html`,
merging the former `algorithm.html` + `results.html` into one page; modeled
on `docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`)

```
+--------------------------------------------------------------------+
| Find duplicate addresses                                             |
|                                                                       |
|  Method [ Nearest Neighbor v ]   Distance function [ Levenshtein v ] |
|  Radius [ 3 ]                                                        |
|  (no submit button here -- any change above live-recomputes the      |
|   table below in place via HTMX, debounced per field change)         |
+--------------------------------------------------------------------+
| Merge? | Candidate addresses              | New cell value | Distance|
+--------+-----------------------------------+-----------------+-------+
| [ ]    | #4  "123 Main St"  (click to use)  | [123 Main St  ] |   2   |
|        | #17 "123 main street" (click)      |                 |       |
+--------+-----------------------------------+-----------------+-------+
| [x]    | #9  "456 Oak Ave" (click)          | [456 Oak Avenue]|   3   |
|        | #22 "456 Oak Avenue" (clicked)     |                 |       |
+--------+-----------------------------------+-----------------+-------+
| [ ]    | #2  "789 Pine Rd"                  | [789 Pine Rd  ] |  (none, fingerprint family -- no Distance column/cell) |
|        | #5  "789 pine rd"                  |                 |       |
+--------+-----------------------------------+-----------------+-------+
|                                                                       |
|  [ Merge selected & re-cluster ]                                     |
+--------------------------------------------------------------------+
```

Key structural points (M4, final):

- **One row = one pair, always.** If A, B, C are all mutually matched, this
  renders as three separate rows (A-B, B-C, A-C), never one 3-member group
  — see `frd.md` FR-4.2/FR-4.4 and `data-dictionary.md`'s `CandidatePair`
  entry.
- **Method** -> **Distance function** -> parameter field is a three-level
  cascade: Distance function options are filtered by Method; the parameter
  field's label ("Radius" vs. "N-Gram size") and presence (omitted entirely
  for plain Fingerprint) depend on the chosen Distance function.
- **Distance column**: present with a numeric value only for
  nearest-neighbor-family pairs (Levenshtein, PPM/NCD); omitted for
  fingerprint-family pairs (no numeric distance exists for those — see
  third example row above).
- **"New cell value"** is always an editable free-text input, pre-filled
  per the click/check interaction rules (`frd.md` FR-5.4/FR-5.5), not
  read-only.
- **No** Select all / Deselect all / Export clusters / Close buttons (all
  present in the OpenRefine reference screenshot) — out of scope for
  AddressRefine. Only "Merge selected & re-cluster" exists.
- On submit, every **checked** row's pair is merged: both underlying rows
  rewritten to that row's current "New cell value" text. A conflict
  (two checked rows disagreeing on the same underlying row's target value)
  blocks the merge entirely with a validation error instead of applying
  anything.
- After a successful merge, the table refreshes in place with the
  currently-selected algorithm/params rerun against the newly-merged data
  — still the same page, no navigation.

## Screen 4 (M2/M3 history) — Results (`results.html` +
`partials/_results_table.html`, `partials/_pair_row.html`; M2 read-only, M3
adds distance column; **superseded M4 — see Screen 3 above**)

```
+--------------------------------------------------------------------+
| Candidate duplicate groups  (algorithm: N-Gram Fingerprint, n=2)      |
|                                                                       |
|  +----------------------------------------------------------------+ |
|  | Group 1                                          [Accept][Reject]| |  <- inert checkboxes/buttons in M2
|  |   Row 4:  "123 Main St"                                          | |
|  |   Row 17: "123 main street"                                     | |
|  +----------------------------------------------------------------+ |
|  +----------------------------------------------------------------+ |
|  | Group 2  (distance: 2)                           [Accept][Reject]| |  <- distance col only for NN algos (M3+)
|  |   Row 9:  "456 Oak Ave"                                          | |
|  |   Row 22: "456 Oak Avenue"                                      | |
|  +----------------------------------------------------------------+ |
+--------------------------------------------------------------------+
```

M2/M3 history only: this page (and the standalone `GET /results` route
that rendered it) is **replaced by Screen 3 above as of M4.** `GET
/results` now redirects to `/algorithm` (`frd.md` FR-3.7/FR-5.1) rather
than rendering its own page. The Accept/Reject buttons shown here were
always inert placeholders (M2/M3) and are not carried forward — M4 has no
per-pair accept/reject concept (`brd.md` G3, `data-dictionary.md`'s
"Dropped in M4" table).

- M2: table rendered `session.candidate_pairs` read-only; no `distance`
  column populated yet (key-collision algorithms only); accept/reject
  controls present in markup but non-functional ("checkboxes inert" per
  the M2 issue).
- M3: a `distance` column appeared for nearest-neighbor algorithm results.
- M5 (upcoming): download-CSV link/button becomes functional on Screen 3,
  pointing at `GET /export.csv`.
