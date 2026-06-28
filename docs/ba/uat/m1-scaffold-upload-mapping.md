# UAT Plan — M1: Scaffold + Upload + Mapping

Status: Backfilled retroactively. This is a manual test script a human (or
the orchestrating session) can run against a live `uvicorn` instance to
confirm M1 behaves as specified, independent of the automated pytest suite.

## Preconditions

- `uvicorn app.main:app --reload` is running locally.
- A test CSV file is available, e.g.:

  ```csv
  ZipCode,StreetAddress,City,Country
  00501,123 Main St,Springfield,USA
  NA,456 Oak Ave,Shelbyville,USA
  ```

  (Saved as `sample.csv` for the steps below; note the deliberately
  leading-zero zip and the literal `"NA"` zip value, matching
  `tests/conftest.py:sample_csv_bytes`.)

## UAT-M1-1: Happy path upload and mapping

1. Navigate to `http://127.0.0.1:8000/`.
2. Confirm the page shows an upload form with a file picker and an
   "Upload" button.
3. Choose `sample.csv` and submit.
4. Expect: browser redirects to `/mapping`; a cookie named
   `addressrefine_session` is now set (check via browser dev tools).
5. Confirm the mapping page lists `ZipCode`, `StreetAddress`, `City`,
   `Country` as options in each of the four dropdowns, and that `Street`
   is pre-selected to `StreetAddress`, `Zip` to `ZipCode`, `City` to
   `City`, `Country` to `Country`.
6. Click "Save mapping" without changing anything.
7. Expect: page reloads at `/mapping`, no error flash shown.

## UAT-M1-2: Reject oversized upload

1. Create or obtain a file larger than 10 MB (e.g. `fsutil file
   createnew big.csv 11000000` on Windows, then rename to `.csv`).
2. From `/`, upload `big.csv`.
3. Expect: page stays on the upload form, shows an error message
   mentioning the file is too large and the 10 MB limit, HTTP 400.

## UAT-M1-3: Reject empty file

1. Create a 0-byte file named `empty.csv`.
2. From `/`, upload it.
3. Expect: error flash shown, stays on upload page, HTTP 400.

## UAT-M1-4: Mapping validation — bad column name

1. Upload `sample.csv` again (fresh upload clears any prior mapping).
2. On the mapping page, use browser dev tools or a raw HTTP client to
   submit `street_col=NotAColumn&zip_col=ZipCode` (bypassing the
   dropdown's real options, simulating a tampered request).
3. Expect: HTTP 422, page re-renders with an error message containing
   "not a column in the uploaded CSV."

## UAT-M1-5: Mapping validation — neither zip nor city

1. Upload `sample.csv`.
2. Submit the mapping form with only `street_col=StreetAddress` and both
   `Zip`/`City` left at "-- none --".
3. Expect: HTTP 422, form re-rendered with a validation error.

## UAT-M1-6: Leading-zero and "NA" preservation (data integrity spot check)

1. Upload `sample.csv`.
2. Save the default (best-guess) mapping.
3. There is no UI yet that surfaces extracted values directly (results
   view doesn't exist until M2) — this step is currently only verifiable
   via the automated test suite (`tests/test_compute/test_pandas_backend.py`)
   or by adding a temporary debug route. Flag this as a manual-UAT gap to
   close once M5's CSV export ships (re-downloading and re-inspecting the
   CSV will close this gap end-to-end).

## Sign-off

M1 UAT is considered passed as of the M1 PR merge to `main` (commit
`7672182`), based on the automated test suite plus ad hoc manual checks
performed by the project owner during that milestone (no formal UAT
record was kept at the time, since this process did not yet exist). This
document exists going forward as the retroactive baseline for the format
later milestones' UAT plans should follow.
