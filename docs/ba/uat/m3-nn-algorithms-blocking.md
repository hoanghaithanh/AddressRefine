# UAT Plan — M3: Nearest-Neighbor Algorithms + Blocking

Milestone branch: `m3-nn-algorithms-blocking`
Status: Written before the `coder` pass. Designed as a manual test
script that a human tester (or the orchestrating session) can execute
against a running `uvicorn app.main:app --reload` instance after the
`coder` and `tester` passes complete. Steps map to the acceptance
criteria in `acceptance-criteria/m3-nn-algorithms-blocking.md`.

## Prerequisites

1. `pip install -r requirements-dev.txt` is up to date (includes
   `rapidfuzz`).
2. `uvicorn app.main:app --reload` is running at `http://localhost:8000`.
3. A test CSV file `uat_m3.csv` is prepared with the following
   characteristics (hand-craft or use a spreadsheet):

```
street,zip,city,country
123 Main St,01234,Springfield,US
123 Main Street,01235,Springfield,US
456 Oak Ave,98765,Portland,US
456 Oak Avenue,98766,Portland,US
789 Pine Rd,,Boston,US
789 Pine Road,,boston,US
Old Lane,,, 
Old Ln,,,
```

   Rationale for this fixture:
   - Rows 0 and 1: same zip prefix (`012`), small edit distance — should
     match under Levenshtein.
   - Rows 2 and 3: same zip prefix (`987`), small edit distance.
   - Rows 4 and 5: blank zip, same city (`boston` after normalization);
     test blocking fallback to city.
   - Rows 6 and 7: blank zip, blank city — go into `__unblocked__` bucket.

---

## Scenario 1 — Levenshtein algorithm, default threshold

**Steps:**
1. Navigate to `http://localhost:8000/`. Upload `uat_m3.csv`.
2. On the mapping page, map: Street = `street`, Zip = `zip`,
   City = `city`, Country = `country`. Submit.
3. On the algorithm page, select "Levenshtein Distance". Leave threshold
   at the default (`3`). Click "Run matching".

**Expected results:**
- Redirect to `/results` (HTTP 303 → 200).
- Results table shows candidate groups. At minimum, rows 0+1 and rows
  2+3 should appear as separate groups (edit distance between "Main St"
  and "Main Street" is within 3 characters after street normalization
  is applied within `rapidfuzz`).
- The distance column shows an integer value for each group (not `"—"`).
- Near the "Distance" column header, the page shows text indicating
  "edit distance" (or equivalent scale label).
- Rows 4+5 may or may not match depending on the edit distance of
  "789 Pine Rd" vs "789 Pine Road" (within 3 chars — should match).
- Rows 6+7 should match if "Old Lane" vs "Old Ln" is within threshold
  (edit distance = 2, so yes at threshold 3).

**Pass criteria:** At least one candidate group is shown; the distance
column shows integers; the scale sub-label is visible; no 500 error.

---

## Scenario 2 — Levenshtein threshold validation

**Steps:**
1. (With an uploaded dataset and confirmed mapping from Scenario 1.)
   Navigate to `/algorithm`.
2. Select "Levenshtein Distance". Enter `threshold = -1`. Submit.

**Expected results:**
- HTTP 422 response; page re-renders with a flash error message
  mentioning `threshold` must be a non-negative integer.
- `session.algorithm_params` is not updated (navigate to `/results` to
  confirm last run's results are unchanged).

3. Now enter `threshold = 2.5`. Submit.

**Expected results:**
- Same: HTTP 422, flash error, no re-run.

4. Now enter `threshold = 0`. Submit.

**Expected results:**
- Accepted (0 is valid for Levenshtein). Redirect to `/results`.
- Results table likely shows fewer or no groups (identical strings only
  match at threshold 0) — verify no 500 error.

**Pass criteria:** Negative and non-integer values rejected with 422;
`0` is accepted; results page loads without error.

---

## Scenario 3 — NCD / PPM algorithm, default threshold

**Steps:**
1. Navigate to `/algorithm`.
2. Select "PPM / NCD". Leave threshold at the default (`3`). Submit.

**Expected results:**
- Redirect to `/results`. Results table shown.
- Distance column shows float values (e.g. `0.12`, `0.27`) for matched
  groups.
- Near the "Distance" column header, page shows "NCD score (0–1)" or
  equivalent.
- No 500 error.

**Pass criteria:** NCD results rendered; float distances visible; scale
label visible.

---

## Scenario 4 — NCD threshold validation

**Steps:**
1. Navigate to `/algorithm`. Select "PPM / NCD".
2. Enter `threshold = 0`. Submit.

**Expected results:**
- HTTP 422, flash error (threshold must be 1–10 for NCD).

3. Enter `threshold = 11`. Submit.

**Expected results:**
- HTTP 422, flash error.

4. Enter `threshold = 10`. Submit.

**Expected results:**
- Accepted. Redirect to `/results`. Results shown (likely many groups
  at high threshold). No 500 error.

**Pass criteria:** `0` and `> 10` rejected; `10` accepted.

---

## Scenario 5 — Blocking: city fallback (rows 4 and 5)

**Steps:**
1. Run Levenshtein with `threshold = 5` (generous).
2. Check results for rows 4 (`789 Pine Rd, , Boston`) and 5 (`789 Pine
   Road, , boston`).

**Expected results:**
- Rows 4 and 5 appear as a matched group (blocked together via city
  `"boston"` after normalization; edit distance of street values is
  within 5).

**Pass criteria:** City-blocked rows appear as a candidate pair.

---

## Scenario 6 — Blocking: `__unblocked__` bucket (rows 6 and 7)

**Steps:**
1. With Levenshtein threshold = 3 results visible, check for rows 6
   (`Old Lane`) and 7 (`Old Ln`).

**Expected results:**
- Rows 6 and 7 appear as a matched group (both in `__unblocked__`
  bucket; edit distance of "Old Lane" vs "Old Ln" = 2, within threshold).

**Pass criteria:** Unblocked rows with close street addresses still match.

---

## Scenario 7 — Transitive union-find clustering

This scenario requires a CSV fixture where A matches B and B matches C
but A does not directly match C (within Levenshtein threshold).

**Steps:**
1. Prepare a small additional CSV or add rows to `uat_m3.csv`:
   ```
   street,zip,city
   abc,10000,X
   abcd,10000,X
   abcde,10000,X
   ```
   With `threshold = 1`: d("abc","abcd") = 1, d("abcd","abcde") = 1,
   d("abc","abcde") = 2 (above threshold).

2. Upload this CSV, map columns, run Levenshtein with `threshold = 1`.

**Expected results:**
- All three rows appear in one candidate group (not two separate pairs).
- `pair.distance` shown is `2` (the max pairwise distance, d("abc","abcde")).

**Pass criteria:** Transitive match produces one group, not two; max
distance is shown.

---

## Scenario 8 — Key-collision algorithm not affected by blocking (no regression)

**Steps:**
1. Navigate to `/algorithm`. Select "Fingerprint". Submit.

**Expected results:**
- `/results` shows candidate groups where addresses normalize to the
  same fingerprint key (if any exist in the test CSV).
- Distance column shows `"—"` for all groups.
- No "edit distance" or "NCD score" sub-label is shown (key-collision
  has no scale).
- No 500 error.

**Pass criteria:** M2 Fingerprint behavior unchanged; no distance
sub-label for key-collision.

---

## Scenario 9 — `pair_id` presence (developer check)

This is a developer/tester check, not a UI-visible scenario.

**Steps:**
1. After any algorithm run, inspect `session.candidate_pairs` via a
   debugging route or directly in the test suite.

**Expected results:**
- Every `CandidatePair` instance has a `pair_id` attribute that is a
  non-empty string.
- All `pair_id` values within the list are unique.

**Pass criteria:** `pair_id` exists and is unique per pair.

---

## Exit criteria for M3 UAT

All nine scenarios pass with no HTTP 500 errors, no silent wrong results
(verified against the known fixture data), and `pytest -q` + `ruff
check .` + `ruff format --check .` all green.
