# Wireframes — AddressRefine

Status: Living document. Last revised: M2 BA pass (2026-06-28). ASCII-art
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

## Shared header / step indicator (`base.html`)

```
+--------------------------------------------------------------------+
| AddressRefine                                                       |
| [1. Upload] [2. Mapping] [3. Algorithm] [4. Results]                |
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

## Screen 3 — Algorithm Selection (`algorithm.html`, planned M2)

```
+--------------------------------------------------------------------+
| Choose a matching algorithm                                          |
|                                                                       |
|  Algorithm   ( ) Fingerprint                                         |
|              (o) N-Gram Fingerprint                                  |
|                                                                       |
|  -- params for selected algorithm, swapped via HTMX --                |
|  +----------------------------------------------------------------+ |
|  | n (n-gram size)   [ 2 ]                                          | |
|  +----------------------------------------------------------------+ |
|                                                                       |
|  [ Run matching ]                                                    |
+--------------------------------------------------------------------+
```

Note: M3 adds two more radio options (Levenshtein Distance, PPM) each with
their own `threshold` param fragment, swapped in via
`GET /algorithm/params` HTMX requests keyed on the selected radio value.

## Screen 4 — Results (`results.html` + `partials/_results_table.html`,
`partials/_pair_row.html`; M2 read-only, M4 interactive)

```
+--------------------------------------------------------------------+
| Candidate duplicate groups  (algorithm: N-Gram Fingerprint, n=2)      |
|                                                                       |
|  +----------------------------------------------------------------+ |
|  | Group 1                                          [Accept][Reject]| |  <- inert checkboxes/buttons in M2
|  |   Row 4:  "123 Main St"                                          | |
|  |   Row 17: "123 main street"                                     | |
|  |   Representative: ( ) Row 4  ( ) Row 17  ( ) Custom: [______]    | |  <- M4 only
|  +----------------------------------------------------------------+ |
|  +----------------------------------------------------------------+ |
|  | Group 2  (distance: 2)                           [Accept][Reject]| |  <- distance col only for NN algos (M3+)
|  |   Row 9:  "456 Oak Ave"                                          | |
|  |   Row 22: "456 Oak Avenue"                                      | |
|  +----------------------------------------------------------------+ |
|                                                                       |
|  [ Merge accepted groups ]   [ Download CSV ]                        |  <- merge button M4, download M5
+--------------------------------------------------------------------+
```

- M2: table renders `session.candidate_pairs` read-only; no `distance`
  column populated yet (key-collision algorithms only); accept/reject
  controls present in markup but non-functional ("checkboxes inert" per
  the M2 issue).
- M3: a `distance` column appears for nearest-neighbor algorithm results.
- M4: accept/reject/representative controls become live (HTMX partial
  swaps per row); merge button appears.
- M5: download-CSV link/button becomes functional, pointing at
  `GET /export.csv`.
