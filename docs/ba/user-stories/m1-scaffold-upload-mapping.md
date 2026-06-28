# User Stories — M1: Scaffold + Upload + Mapping

Status: Backfilled retroactively (M1 shipped before the BA process existed;
this file documents what M1 actually built, not a forward-looking plan).

## US-M1-1: Upload a CSV of addresses

As a user with a CSV file of address records, I want to upload it to
AddressRefine, so that I can start working with it in the app.

- Branch/PR: M1 committed directly to `main` (predates the
  feature-branch-per-milestone convention).
- Related routes: `GET /`, `POST /upload`.

## US-M1-2: Be protected from accidentally uploading something unusable

As a user, I want the app to reject files that are empty, unparseable, or
too large, with a clear message, so that I don't proceed into the workflow
with a broken dataset.

- Related routes: `POST /upload`.
- Related config: `Settings.MAX_UPLOAD_BYTES` (10 MB).

## US-M1-3: Map my CSV's columns to the fields AddressRefine understands

As a user, I want to tell the app which of my CSV's columns are the street
address, zip, city, and country, so that later matching steps know what to
compare.

- Related routes: `GET /mapping`, `POST /mapping`.
- Related model: `ColumnMapping` (`app/models/domain.py`).

## US-M1-4: Get a head start on mapping via best-guess pre-fill

As a user, I want the app to pre-select likely columns based on their
names (e.g. a header containing "zip"), so that I don't have to map every
column manually when the names are already self-describing.

- Related code: `app/routers/mapping.py:_best_guess_mapping`.

## US-M1-5: Not lose my mapping choice when revisiting the page

As a user who has already confirmed a column mapping, I want returning to
the mapping page to show my saved choice rather than recomputing a fresh
best guess, so that an intentional non-obvious mapping (e.g. picking a
column the best-guess heuristic wouldn't have picked) isn't silently
overwritten.

- Related code: `app/routers/mapping.py:mapping_form` (`session.mapping or
  _best_guess_mapping(headers)`).

## US-M1-6: Be stopped from saving an invalid mapping

As a user, I want the app to reject a mapping submission if I leave street
blank, omit both zip and city, or pick a column name that isn't actually in
my CSV, so that I don't carry an invalid mapping into matching (which would
otherwise fail with a confusing internal error later).

- Related code: `app/models/schemas.py:MappingForm`,
  `app/routers/mapping.py:mapping_submit` (per-column header validation
  loop).
