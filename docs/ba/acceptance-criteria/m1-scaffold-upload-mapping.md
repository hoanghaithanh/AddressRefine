# Acceptance Criteria — M1: Scaffold + Upload + Mapping

Status: Backfilled retroactively, derived from M1's actual shipped
behavior (`app/routers/upload.py`, `app/routers/mapping.py`,
`app/compute/pandas_backend.py`) and its existing test suite
(`tests/test_routers/test_upload.py`, `tests/test_routers/test_mapping.py`,
`tests/test_compute/test_pandas_backend.py`). Acceptance criteria below
are stated as already-met (M1 is closed/merged), each annotated with the
test that verifies it.

## AC-M1-1 — Upload form renders

Given a fresh session, when the user requests `GET /`, then the response
is HTTP 200 and contains a `<form>` whose action is `/upload`.

- Verified by: `tests/test_routers/test_upload.py::test_get_upload_form_returns_200_with_form`

## AC-M1-2 — Valid CSV upload redirects to mapping and sets a session cookie

Given a well-formed CSV under the size limit, when the user `POST`s it to
`/upload`, then the response is HTTP 303 redirecting to `/mapping`, and the
response sets a cookie named `Settings.SESSION_COOKIE_NAME`.

- Verified by: `tests/test_routers/test_upload.py::test_post_upload_valid_csv_redirects_to_mapping_and_sets_cookie`

## AC-M1-3 — Oversized upload is rejected without buffering the whole file

Given a file larger than `Settings.MAX_UPLOAD_BYTES` (10 MB), when the user
`POST`s it to `/upload`, then the response is HTTP 400 with a message
containing "too large", and the size check happens via chunked reads (1 MB
at a time) rather than reading the entire payload into memory first.

- Verified by: `tests/test_routers/test_upload.py::test_post_upload_oversized_file_does_not_redirect`

## AC-M1-4 — Empty/unparseable CSV is rejected

Given an empty file body, when the user `POST`s it to `/upload`, then the
response is HTTP 400 and contains a flash/error indication in the rendered
HTML.

- Verified by: `tests/test_routers/test_upload.py::test_post_upload_garbage_empty_csv_returns_400`

## AC-M1-5 — CSV with header row but zero data rows is rejected

Given CSV bytes containing only a header line, when
`PandasComputeBackend.load_csv` parses it, then it raises `ValueError`
(because `frame.shape[0] == 0`).

- Verified by: `tests/test_compute/test_pandas_backend.py::test_load_csv_header_only_raises_value_error`

## AC-M1-6 — Leading zeros in zip-like columns are preserved

Given a CSV row with a zip value of `"00501"`, when the row is loaded and
then extracted via `extract_columns`, then the extracted zip string is
exactly `"00501"` (not coerced to the integer `501`).

- Verified by: `tests/test_compute/test_pandas_backend.py::test_extract_columns_preserves_leading_zero_zip`

## AC-M1-7 — Literal "NA" address tokens are preserved, not coerced to NaN

Given a CSV row with a zip value of the literal string `"NA"`, when the
row is loaded and extracted, then the extracted zip string is exactly
`"NA"` (not Python `None`/`NaN`).

- Verified by: `tests/test_compute/test_pandas_backend.py::test_extract_columns_preserves_literal_na_string`

## AC-M1-8 — Unmapped logical columns extract as empty string, not null

Given a `ColumnMapping` with `zip_col=None, city_col=None, country_col=None`
(only `street_col` set), when `extract_columns` runs, then each unmapped
logical field's value is `""` for every row (never `None`).

- Verified by: `tests/test_compute/test_pandas_backend.py::test_extract_columns_unmapped_logical_column_is_empty_string`

## AC-M1-9 — Mapping page shows uploaded headers with a best-guess pre-fill

Given a dataset has been uploaded with headers `ZipCode, StreetAddress,
City, Country`, when the user requests `GET /mapping` without having
submitted a mapping yet, then the response is HTTP 200, lists all four
headers, and pre-selects `StreetAddress` for street, `ZipCode` for zip,
`City` for city, `Country` for country (substring-match best guess).

- Verified by: `tests/test_routers/test_mapping.py::test_get_mapping_after_upload_shows_headers_with_best_guess_selected`

## AC-M1-10 — Mapping page redirects to upload if no dataset exists yet

Given a session with no uploaded dataset, when the user requests `GET
/mapping`, then the response is HTTP 303 redirecting to `/`.

- Verified by: `tests/test_routers/test_mapping.py::test_get_mapping_without_upload_redirects_to_root`

## AC-M1-11 — Valid mapping submission is accepted

Given an uploaded dataset, when the user `POST`s `/mapping` with a valid
`street_col` and at least one of `zip_col`/`city_col` set to real headers,
then the response is HTTP 303 redirecting to `/mapping` (current M1
behavior; expected to change to `/algorithm` once M2 ships — see drift note
below).

- Verified by: `tests/test_routers/test_mapping.py::test_post_mapping_valid_redirects`

## AC-M1-12 — Mapping submission with a non-existent street column is rejected

Given an uploaded dataset, when the user `POST`s `/mapping` with
`street_col` set to a value that is not one of the real CSV headers, then
the response is HTTP 422 and contains "not a column" (case-insensitive).

- Verified by: `tests/test_routers/test_mapping.py::test_post_mapping_street_col_not_a_real_header_returns_422`

## AC-M1-13 — Mapping submission with a non-existent zip column is rejected

Given an uploaded dataset, when the user `POST`s `/mapping` with a valid
`street_col` but a `zip_col` value that is not a real header, then the
response is HTTP 422 and contains "not a column". (This is the regression
test for the bug noted in `CLAUDE.md`: every mapped column, not just
`street_col`, must be validated.)

- Verified by: `tests/test_routers/test_mapping.py::test_post_mapping_zip_col_not_a_real_header_returns_422`

## AC-M1-14 — Mapping submission with neither zip nor city is rejected

Given an uploaded dataset, when the user `POST`s `/mapping` with
`street_col` set but both `zip_col` and `city_col` omitted, then the
response is HTTP 422.

- Verified by: `tests/test_routers/test_mapping.py::test_post_mapping_without_zip_or_city_returns_422`

## AC-M1-15 — A previously-saved mapping is shown on return visits, not recomputed

Given a user has already submitted a mapping that differs from the
best-guess pre-fill (e.g. mapping `street_col` to a column named `"City"`),
when the user requests `GET /mapping` again, then the page reflects the
saved mapping (`"City"` selected for street), not the best-guess default
(`"StreetAddress"` is not selected).

- Verified by: `tests/test_routers/test_mapping.py::test_post_mapping_then_get_shows_chosen_mapping_not_best_guess`

## Notes on scope not covered by AC (documented v1 tradeoffs, not gaps)

- `ComputeBackend.replace_values` is intentionally unimplemented in M1
  (`raise NotImplementedError`), verified by
  `tests/test_compute/test_pandas_backend.py::test_replace_values_raises_not_implemented`.
  Real implementation is M4 scope.
- No algorithm, results, or merge functionality exists yet; those are M2-M4
  scope and have their own acceptance-criteria files.
