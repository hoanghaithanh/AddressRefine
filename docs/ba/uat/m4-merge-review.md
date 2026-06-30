# UAT Plan — M4: Combined Algorithm/Results Page + Pairwise Merge

Milestone branch: `m4-merge-review`
Status: Written before the `coder` pass. Designed as a manual test script
that a human tester (or the orchestrating session) can execute against a
running `uvicorn app.main:app --reload` instance after the `coder` and
`tester` passes complete. Steps map to the acceptance criteria in
`acceptance-criteria/m4-merge-review.md`.

## Prerequisites

1. `pip install -r requirements-dev.txt` is up to date.
2. `uvicorn app.main:app --reload` is running at `http://localhost:8000`.
3. A test CSV file `uat_m4.csv` is prepared:

```
street,zip,city,country
123 Main St,01234,Springfield,US
123 main street,01235,Springfield,US
abc,10000,X,US
abcd,10000,X,US
abcde,10000,X,US
456 Oak Ave,98765,Portland,US
456 Oak Avenue,98765,Portland,US
789 Pine Rd,55555,Lakeview,US
789 PINE RD,55556,Lakeview,US
```

   Rationale for this fixture:
   - Rows 0–1: small Levenshtein edit distance, same zip-prefix block —
     should match under Levenshtein with a generous Radius.
   - Rows 2–4 (`abc`/`abcd`/`abcde`): the classic M3 transitive-clustering
     fixture (d(abc,abcd)=1, d(abcd,abcde)=1, d(abc,abcde)=2). Under M4
     these must render as **two** separate rows (abc-abcd, abcd-abcde) at
     Radius=1, never a 3-member group and never a synthesized abc-abcde
     row.
   - Rows 5–6: identical-after-fingerprint-normalization street values
     (`"456 Oak Ave"` vs `"456 Oak Avenue"` differ enough that fingerprint
     keys differ — use this pair primarily for the Levenshtein/NN
     Distance-column check instead).
   - Rows 7–8: differ only by case/punctuation — should collide under
     plain Fingerprint, exercising the pairwise-explode behavior if a
     3rd duplicate is added (see Scenario 4 below, which adds one).

---

## Scenario 1 — Combined page renders Method -> Distance function -> parameter cascade

**Steps:**
1. Navigate to `http://localhost:8000/`. Upload `uat_m4.csv`.
2. On the mapping page, map: Street = `street`, Zip = `zip`, City = `city`,
   Country = `country`. Submit.
3. Land on the combined algorithm-and-results page (`/algorithm`).

**Expected results:**
- Step indicator shows 3 steps (`Upload`, `Mapping`, `Algorithm & Results`)
  — not 4.
- A "Method" field offers "Nearest Neighbor" and "Fingerprint".
- Selecting "Nearest Neighbor" shows a "Distance function" field offering
  "Levenshtein" and "PPM (NCD)".
- Selecting "Fingerprint" as Method shows "Fingerprint" and "N-Gram
  Fingerprint" as Distance function options.
- With "Levenshtein" or "PPM (NCD)" selected, a field labeled "Radius" is
  shown.
- With "Fingerprint" selected, no parameter field is shown at all.
- With "N-Gram Fingerprint" selected, a field labeled "N-Gram size" is
  shown.

**Pass criteria:** All cascade combinations render the correct
field/label/presence; no 500 error.

---

## Scenario 2 — Live recompute with no submit button

**Steps:**
1. From the combined page, select Method = "Nearest Neighbor", Distance
   function = "Levenshtein", Radius = `5`.
2. Observe the results table populate without clicking any button.
3. Change Radius to `1`.
4. Change Distance function to "PPM (NCD)".
5. Change Method to "Fingerprint".

**Expected results:**
- After step 1, the table updates automatically (HTMX request observable
  in browser dev tools as a partial-content response, not a full page
  navigation — URL bar does not change).
- After step 3 (narrower Radius), fewer or equal rows are shown compared
  to step 1, and the page does not reload.
- After step 4, the table updates to reflect NCD-scored pairs.
- After step 5, the table updates to reflect Fingerprint-family pairs
  (Distance column no longer shows numeric values for these rows).
- No "Run matching" button exists anywhere on the page.

**Pass criteria:** Every control change triggers a table refresh with no
full page reload and no explicit submit click.

---

## Scenario 3 — Every row is exactly one pair (transitive fixture)

**Steps:**
1. Select Method = "Nearest Neighbor", Distance function = "Levenshtein",
   Radius = `1`.
2. Locate rows for `abc`, `abcd`, `abcde` (originally rows 2, 3, 4 of the
   CSV) in the results table.

**Expected results:**
- Exactly two rows appear: one pairing `abc`/`abcd`, one pairing
  `abcd`/`abcde`.
- No row pairs `abc` directly with `abcde` (their edit distance is 2,
  above the Radius=1 cutoff — and even though they're "transitively"
  connected via `abcd`, M4 does not synthesize that pair).
- No single row lists all three values together.
- Each of the two rows shows a numeric Distance value of `1`.

**Pass criteria:** Exactly 2 rows for this fixture, both with distance 1,
no 3-member row, no synthesized abc-abcde row.

---

## Scenario 4 — Fingerprint cluster of 3 explodes into 3 pairwise rows

**Steps:**
1. Add a 10th row to `uat_m4.csv` (or a fresh small CSV): a third address
   that fingerprint-normalizes identically to rows 7–8 (e.g. `"PINE RD
   789"` — same token multiset as `"789 PINE RD"` after fingerprint
   normalization: lowercase, strip punctuation, dedupe+sort tokens).
   Re-upload, re-map.
2. Select Method = "Fingerprint", Distance function = "Fingerprint".

**Expected results:**
- All three rows (789 Pine Rd / 789 PINE RD / PINE RD 789) share one
  fingerprint key.
- The results table shows exactly **3** rows for this trio (every pairwise
  combination), not one 3-member group.
- None of the 3 rows shows a numeric Distance value (Distance column is
  omitted/blank for fingerprint-family pairs — not "0", not "—").

**Pass criteria:** Exactly 3 pairwise rows for the 3-way fingerprint
cluster; no Distance values shown.

---

## Scenario 5 — Click an address to default "New cell value" and auto-check "Merge?"

**Steps:**
1. With any non-empty results table showing, locate a row with two
   candidate addresses.
2. Click the second-listed address in that row.

**Expected results:**
- "New cell value" for that row immediately updates to show the clicked
  address's text.
- The row's "Merge?" checkbox becomes checked.
- No network request occurs for this interaction (purely client-side;
  observable via dev tools — no new HTTP request fires).

**Pass criteria:** Click sets value + checks box, instantly, no request.

---

## Scenario 6 — Check "Merge?" without clicking defaults to the first address

**Steps:**
1. Locate a different row (not yet interacted with) in the results table.
2. Check its "Merge?" checkbox directly (without clicking either address
   first).

**Expected results:**
- "New cell value" updates to show the row's first-listed address.
- The checkbox is checked.

**Pass criteria:** Checking without a prior click defaults to the first
address.

---

## Scenario 7 — "New cell value" remains freely editable

**Steps:**
1. Using either row from Scenario 5 or 6, click into "New cell value" and
   type a custom string, e.g. `"789 Pine Road"`.

**Expected results:**
- The input accepts the typed text and shows it (not reset back to the
  clicked/defaulted value).
- "Merge?" remains checked.

**Pass criteria:** Field is freely editable; checkbox state unaffected by
typing.

---

## Scenario 8 — Successful merge rewrites both rows and reruns matching

**Steps:**
1. Check "Merge?" on the row from Scenario 5 (address clicked, "New cell
   value" set to the clicked address's text). Leave other rows unchecked.
2. Click "Merge selected & re-cluster".

**Expected results:**
- No full page reload (or, if a reload occurs, it lands back on
  `/algorithm`, not a separate page).
- The results table refreshes; the merged pair's two rows no longer appear
  in the table (since both underlying rows now share the same value).
- A re-run of the currently selected algorithm/params happened
  automatically (verify by checking other previously-shown rows are still
  present/expected, confirming a real rerun occurred rather than a static
  removal).
- No error message is shown.

**Pass criteria:** Merge succeeds silently, table refreshes with merged
rows gone, no error.

---

## Scenario 9 — Conflict blocks the merge entirely

**Steps:**
1. Reload `/algorithm` with a fresh Radius/Distance function selection
   that produces at least two overlapping pairs sharing one underlying row
   (e.g. using the `abc`/`abcd`/`abcde` fixture at Radius=1: row "abc-abcd"
   and row "abcd-abcde" both involve `abcd`).
2. Check "Merge?" on "abc-abcd" and set "New cell value" to `"abc"`.
3. Check "Merge?" on "abcd-abcde" and set "New cell value" to `"abcde"`.
   (Both rows target the underlying `abcd` row, with disagreeing values
   `"abc"` vs `"abcde"`.)
4. Click "Merge selected & re-cluster".

**Expected results:**
- The merge is blocked: a validation error is shown identifying the
  conflicting row (`abcd`'s row index) and its two disagreeing target
  values (`"abc"` and `"abcde"`).
- No row's underlying value changes (reload the page and confirm `abc`,
  `abcd`, `abcde` are all still present, unmodified, in the dataset).
- No new dataset version was created (if a version/debug indicator is
  available; otherwise verify indirectly by confirming row count and
  values are unchanged).

**Pass criteria:** Merge is blocked with a clear conflict message; nothing
mutated.

---

## Scenario 10 — Zero checked rows is a harmless no-op

**Steps:**
1. With a non-empty results table and nothing checked, click "Merge
   selected & re-cluster".

**Expected results:**
- No error is shown.
- The table is unchanged.
- No 500 error.

**Pass criteria:** Clicking with nothing checked does nothing, silently.

---

## Scenario 11 — No accept/reject controls anywhere

**Steps:**
1. Inspect the combined page's HTML/visible controls across all four
   algorithm/distance-function combinations.

**Expected results:**
- No "Accept" or "Reject" button/control exists anywhere on the page.
- No "representative value" mode toggle (radio buttons for "original" vs.
  "custom") exists — only the single "New cell value" text input per row.
- No "Select all" / "Deselect all" / "Export clusters" / "Close" buttons
  exist.

**Pass criteria:** Only "Merge?" checkbox, clickable addresses, "New cell
value" input, and the single "Merge selected & re-cluster" button are
present as interactive elements.

---

## Scenario 12 — `GET /results` redirects (no dead link / 404)

**Steps:**
1. With an active session, manually navigate the browser to
   `http://localhost:8000/results`.

**Expected results:**
- The browser is redirected to `/algorithm` (HTTP 303), landing on the
  combined page — not a 404, not a separately rendered page.

**Pass criteria:** `/results` is a working redirect, not a dead route.

---

## Exit criteria for M4 UAT

All twelve scenarios pass with no HTTP 500 errors, no silent wrong results
(verified against the known fixture data), and `pytest -q` + `ruff
check .` + `ruff format --check .` all green.
