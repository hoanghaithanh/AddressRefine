# UAT Plan — M2: Fingerprint + N-Gram Fingerprint Algorithms + Read-Only Results

Status: Forward-looking manual test script, to be run against a live
`uvicorn` instance once the `coder`/`tester` passes for M2 are complete.
Reuses the plan's "Verification" section guidance (try each algorithm,
inspect results) at M2's scope (Fingerprint/N-Gram only; Levenshtein/PPM
arrive in M3).

## Preconditions

- `uvicorn app.main:app --reload` running locally.
- A CSV with deliberate near-duplicates at the token level, e.g.:

  ```csv
  ZipCode,StreetAddress,City,Country
  00501,123 Main St,Springfield,USA
  00501,St Main 123,Springfield,USA
  00502,456 Oak Ave,Shelbyville,USA
  00503,789 Pine Rd,Capital City,USA
  ```

  (Rows 1 and 2 are token-identical after normalization — should cluster
  under plain Fingerprint. Rows 3 and 4 should not cluster with anything.)

## UAT-M2-1: Fingerprint algorithm groups token-identical addresses

1. Upload the sample CSV above, confirm mapping (Street ->
   StreetAddress, Zip -> ZipCode), and submit the mapping form.
2. Expect: submitting the mapping form lands on `/algorithm` directly
   (not back on `/mapping`) — see AC-M2-24.
3. On `/algorithm`, select "Fingerprint", submit.
4. Expect: redirected/rendered to `/results` showing exactly one group
   containing rows 1 and 2 ("123 Main St" / "St Main 123"), with a blank
   `distance` cell for that group (key-collision algorithms never
   populate distance — see AC-M2-21a); rows 3 and 4 do not appear in any
   group.

## UAT-M2-2: N-Gram Fingerprint with default n=2 catches the same pair

1. From `/algorithm`, select "N-Gram Fingerprint", leave `n` at its
   default (2), submit.
2. Expect: results show rows 1 and 2 grouped (same as Fingerprint, since
   tokens are character-identical once spaces are stripped).

## UAT-M2-3: Changing n changes (or at least re-runs) the grouping

1. From `/algorithm`, select "N-Gram Fingerprint", set `n` to `4`,
   submit.
2. Expect: results page re-renders (confirms the param actually reaches
   the algorithm); manually verify the grouping is still sensible for
   `n=4` on this sample (rows 1/2 likely still group, since they're
   character-identical once normalized).

## UAT-M2-4: Switching algorithms refreshes results without re-uploading

1. With results showing for Fingerprint, navigate back to `/algorithm`
   and switch to N-Gram Fingerprint.
2. Expect: no need to re-upload or re-map; results update to reflect the
   newly selected algorithm.

## UAT-M2-5: Accept/Reject controls are visibly present but inert

1. On the `/results` page, locate the Accept/Reject controls for a
   group.
2. Click them.
3. Expect: no visible state change, no network request that mutates
   server state (verify via browser dev tools Network tab) — consistent
   with the M2 issue's explicit "checkboxes inert" requirement. (If the
   coder chooses to omit the controls entirely rather than render them
   inert, that's also acceptable per a literal reading of "read-only
   results view" — confirm whichever choice was made matches what ships.)

## UAT-M2-6: No empty-CSV/no-mapping edge cases regress

1. Without uploading anything, navigate directly to `/algorithm`.
2. Expect: redirected to `/mapping` (or `/`, if no dataset at all),
   not a 500 error.

## UAT-M2-7: Invalid `n` is rejected with a clear error

1. Upload the sample CSV, confirm mapping.
2. On `/algorithm`, select "N-Gram Fingerprint", set `n` to `0`, submit.
3. Expect: HTTP 422 (visible as the form re-rendering with a flash error
   in the browser), the error message indicates `n` must be a positive
   integer, and no results are computed/persisted from this submission
   (see AC-M2-25). Repeat with `n = -1` and a non-numeric value (e.g.
   `abc`) and confirm the same outcome.

## UAT-M2-8: Empty results show an actionable message

1. Upload a CSV where every street address is distinct enough that no
   algorithm will cluster any rows (e.g. four wildly different
   addresses, no shared tokens or n-grams).
2. Confirm mapping, then on `/algorithm` select "Fingerprint", submit.
3. Expect: `/results` shows no group rows, but does show an explicit
   message stating no candidate duplicates were found and suggesting the
   user try a different algorithm or adjust parameters (not a silently
   bare/empty table) — see AC-M2-26.

## Sign-off

To be completed once the M2 `coder`/`tester` passes land and this UAT
script is actually executed; results to be recorded here (or in the PR
description) before the M2 PR is merged.
