# User Stories — M4: Combined Algorithm/Results Page + Pairwise Merge

Milestone branch: `m4-merge-review`
Status: Written before the `coder` pass. Source: GitHub issue #3 (title
predates this scope — see "Plan/issue drift" note in
`acceptance-criteria/m4-merge-review.md`), the M4 scope redesign resolved
via direct user Q&A with the orchestrating session, and
`docs/design/reference/screenshots/AlgorithmSelectionAndResult.png`
(OpenRefine's cluster/merge dialog).

---

## US-M4-1 — Choose how matches are found, all in one place

**As a** data steward cleaning an address CSV,
**I want to** pick a Method (Nearest Neighbor or Fingerprint), then a
Distance function appropriate to that Method, then a single parameter
field if the chosen function needs one,
**so that** I don't have to navigate to a separate page just to see how my
algorithm choice affects the candidate matches.

**Acceptance notes:**
- Method -> Distance function -> parameter field is a three-level cascade;
  the Distance function dropdown only ever shows options valid for the
  current Method.
- The parameter field's label changes per Distance function ("Radius" for
  Levenshtein/PPM, "N-Gram size" for N-Gram Fingerprint) and is omitted
  entirely for plain Fingerprint, which has no parameter.
- This replaces M2/M3's separate `algorithm.html` page and flat
  single-select Algorithm field.

---

## US-M4-2 — See match results update instantly as I tune the algorithm

**As a** data steward exploring which algorithm/parameters work best for
my dataset,
**I want** the candidate-match table to update immediately whenever I
change Method, Distance function, Radius, or N-Gram size,
**so that** I can iterate quickly without clicking a "Run matching" button
and waiting for a page reload each time.

**Acceptance notes:**
- Implemented as HTMX-triggered partial swaps, not a manual JS `fetch()`
  and not a full page reload.
- An invalid parameter value (e.g. negative Radius) shows an inline/flash
  error without destroying the previously-valid table.

---

## US-M4-3 — Review one duplicate pair at a time, never a tangled multi-row group

**As a** data steward reviewing candidate matches,
**I want** every row of the results table to represent exactly one pair of
two addresses,
**so that** I can decide on each pairwise relationship independently
instead of being forced to accept or reject an entire transitively-linked
cluster as a unit.

**Acceptance notes:**
- If A, B, and C are all mutually matched, this shows as three separate
  rows (A-B, B-C, A-C), not one 3-member group.
- For nearest-neighbor algorithms, this is a natural consequence of
  showing each algorithm-returned pair directly (no transitive clustering
  applied) — there is no "out of radius" pair hidden anywhere, since A-C
  was never returned by the algorithm in the first place if it's not
  within radius.
- For fingerprint-family algorithms, same-key clusters are exploded into
  every pairwise combination, since same-key equality is itself the match
  condition (no separate distance check or "is this pair within range"
  question applies).

---

## US-M4-4 — Quickly merge a pair using one of its existing values

**As a** data steward who agrees that two addresses in a row are
duplicates and is happy to keep one of the two values as-is,
**I want to** click on the address I prefer,
**so that** the row gets pre-filled with that value and marked for merging
in a single click, without typing anything.

**Acceptance notes:**
- Clicking either address sets "New cell value" to that address's text and
  auto-checks "Merge?" for that row.
- This works regardless of the checkbox's current state (clicking an
  address always results in checked + that value).

---

## US-M4-5 — Merge a pair without caring which exact value wins

**As a** data steward who just wants two duplicate rows consolidated and
doesn't care which of the two original spellings is kept,
**I want to** simply check the "Merge?" box without clicking either
address,
**so that** the row defaults to a sensible value (the first-listed
address) without requiring me to make an extra choice.

**Acceptance notes:**
- Checking "Merge?" without a prior address click defaults "New cell
  value" to the row's first-listed address.
- This is purely a default — the value is still editable afterward.

---

## US-M4-6 — Type a custom merged value that doesn't match either original

**As a** data steward who knows the "correct" canonical address isn't
exactly what either matched row currently says (e.g. both have a typo, or
I want to standardize formatting),
**I want to** freely edit the "New cell value" text field for any row,
**so that** I can specify exactly what the merged result should look like,
not just pick between the two existing options.

**Acceptance notes:**
- "New cell value" is always a free-text input, never read-only, even
  after being pre-filled by a checkbox-check or an address click.
- Editing it does not uncheck "Merge?" or otherwise reset the row.

---

## US-M4-7 — Merge several agreed-upon pairs in one action

**As a** data steward who has reviewed multiple rows and decided which
ones to merge,
**I want to** check "Merge?" on each pair I want consolidated and then
click a single "Merge selected & re-cluster" button,
**so that** I can batch-apply my decisions in one step rather than
confirming each pair individually.

**Acceptance notes:**
- Only checked rows are included in the merge; unchecked rows are left
  alone (no implicit "everything not rejected gets merged" behavior, since
  there is no reject concept at all).
- No Select all / Deselect all / Export clusters / Close buttons exist —
  those OpenRefine-dialog extras are out of scope.

---

## US-M4-8 — Be protected from accidentally overwriting an address two different ways

**As a** data steward who might check two overlapping pairs with
conflicting "New cell value" entries by mistake (e.g. row A-B says merge
to "B", row A-C says merge to "C", and both target row A),
**I want** the system to refuse to apply either merge and tell me exactly
which row and which conflicting values caused the problem,
**so that** I don't end up with an unpredictable or silently-chosen result
for row A.

**Acceptance notes:**
- The merge is blocked entirely (nothing mutated, no new dataset version)
  if any conflict exists across the checked rows in this submission.
- The validation error identifies the conflicting underlying row and its
  disagreeing target values, so I can fix my checkbox/text-field
  selections and resubmit.
- This is final, deliberate behavior — not a "last write wins" or
  "first write wins" resolution.

---

## US-M4-9 — See the dataset and results refresh automatically after a merge

**As a** data steward who just merged some duplicate pairs,
**I want** the dataset to be rewritten and the candidate-match table to
refresh immediately with the new data,
**so that** I can keep iterating (find more duplicates, merge again)
without manually re-triggering a rerun or reloading the page.

**Acceptance notes:**
- A successful merge appends a new, immutable `DatasetVersion`
  (`created_from_merge=True`) and reruns matching using whichever
  algorithm/parameters were selected at merge time (not reset to
  defaults).
- Clicking "Merge selected & re-cluster" with nothing checked is a
  harmless no-op — no error, no version appended, table unchanged.

---

## US-M4-10 — Understand a pair's similarity score when one exists

**As a** data steward reviewing a nearest-neighbor-algorithm result,
**I want to** see a numeric "Distance" value for that pair,
**so that** I can judge how confident to be about merging it.

**Acceptance notes:**
- The Distance column shows a value only for nearest-neighbor-family pairs
  (Levenshtein, PPM/NCD); it is omitted for fingerprint-family pairs,
  which have no numeric distance to show (same-key equality is itself the
  match condition).
- Unlike M3, this value is always the single pairwise distance for that
  exact pair — never a cluster maximum, since M4 has no clusters.
