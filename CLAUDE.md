# AddressRefine

A FastAPI app that lets a user upload a CSV of addresses, map its columns (zip/street/city/country), run a fuzzy-matching algorithm (Fingerprint, N-Gram Fingerprint, Levenshtein, PPM/NCD) to find rows that are the same real-world address in different formats, review/accept candidate matches, pick a representative value per match, and merge — which rewrites the dataset and reruns matching.

Full architecture/design rationale lives in the original plan at `C:\Users\hoang\.claude\plans\i-want-to-build-vivid-dijkstra.md` if deeper history is ever needed; this file tracks the current, living state of the codebase.

## Setup (Windows / PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Common commands

```powershell
uvicorn app.main:app --reload      # run the dev server
pytest -q                          # run tests
ruff check .                       # lint
ruff format --check .              # format check
```

## Architecture

- **Server-rendered, no SPA**: Jinja2 templates (`app/templates/`) + HTMX for partial-page interactivity. Full pages extend `base.html`; small fragments live under `templates/partials/` and are returned directly by routes that handle HTMX-triggered actions (accept/reject a pair, swap algorithm params, etc., once those milestones exist).
- **In-memory session state, no DB**: `app/session.py` holds a process-wide `SessionStore` (`dict[str, Session]`), keyed by an httponly cookie set in `app/deps.py:get_session`. One session = one user's working dataset. This is a deliberate v1 simplification — state is lost on restart, and only one session worth of meaningful work is expected at a time.
- **`compute/` vs `algorithms/` seam (the most important boundary in this codebase)**: `app/compute/backend.py` defines `ComputeBackend`, an ABC whose methods take/return `Any` for the dataframe type — never `pandas.DataFrame` in the signature itself. `app/compute/pandas_backend.py` is the only file allowed to import `pandas` and know about `DataFrame` internals. The reason: a future Spark backend should be addable by writing one new file implementing `ComputeBackend`, without touching matching/algorithm code at all. Matching logic only ever receives plain Python dicts (`row_index -> str`) handed to it by a compute backend — it must never see a DataFrame.
- **Routers are thin**: routers parse/validate input, pull data via `get_compute_backend()`, mutate `Session`, and render a template or redirect. Business logic (CSV parsing rules, matching, merging) belongs in `app/services/` (added from Milestone 2 onward), not in router functions.

## Conventions

- **CSV reading**: always `pd.read_csv(..., dtype=str, keep_default_na=False)`. This is deliberate, not an oversight — it preserves leading zeros in zip codes (`"00501"`) and stops literal `"NA"` address tokens from being coerced to `NaN`. Don't "simplify" this away.
- **Column mapping validation**: every mapped column (`street_col`, `zip_col`, `city_col`, `country_col`), not just `street_col`, must be checked against the real CSV headers before being saved to `session.mapping`. An unvalidated optional column will `KeyError` later inside `ComputeBackend.extract_columns`. (This was a real bug found and fixed during M1 review — don't reintroduce it when adding new mapped fields.)
- **Cookie handling**: routes return `Response` objects directly (`TemplateResponse`/`RedirectResponse`), which means FastAPI does **not** merge headers set on a `Depends(get_session)`-injected `Response` into the route's own returned response. The pattern used here: `get_session` stashes a freshly-created session id on `request.state.new_session_id`; a single global middleware in `app/main.py` applies the cookie to whatever response object actually gets returned. If you add a new router, you don't need to do anything special — the middleware covers it automatically.
- **Algorithms are backend-agnostic** (from Milestone 2 onward): `MatchingAlgorithm` implementations in `app/algorithms/` operate on `dict[int, str]`/`dict[str, list[int]]`, never on a DataFrame. If a new algorithm needs row metadata beyond the street address, extend `ComputeBackend.extract_columns`'s output shape, not the algorithm's input type.
- **Upload size limit**: enforced by reading the upload in chunks and aborting as soon as the running total exceeds `settings.MAX_UPLOAD_BYTES` (10 MB) — not by reading the whole file first and checking after. Keep this streaming-check pattern for any future upload-like endpoint.

## Known v1 tradeoffs (intentional, not bugs)

- Single in-memory session, no auth, no persistence across restarts.
- `DatasetVersion` stores a full DataFrame snapshot per version (post-merge) rather than a diff — fine at CSV scale, would need rethinking for very large datasets.
- Local pandas only; no Spark backend yet (the `ComputeBackend` seam exists specifically so this can be added later without touching algorithms/services).
- Remote Spark / Microsoft Fabric is explicitly out of scope.

## Workflow

This project is built milestone-by-milestone (see the plan file above for the full breakdown: M1 scaffold+upload+mapping, M2 key-collision algorithms, M3 nearest-neighbor algorithms+blocking, M4 review/merge, M5 export+CI). Each milestone goes through a coder pass, then a tester pass, then a senior-dev review pass before moving to the next one.

## GitHub repo conventions

- **Repo**: https://github.com/hoanghaithanh/AddressRefine (public). Remote `origin` uses SSH.
- **Branching, from M2 onward**: one feature branch per milestone (e.g. `m2-fingerprint-algorithms`), opened as a PR linked to that milestone's issue. The senior-dev review pass posts its findings as PR comments before merge. M1 was the exception — it was committed directly to `main` before this convention was adopted.
- **Branch protection on `main`**: PRs required for all changes (no direct pushes), no force-push, no branch deletion. `required_approving_review_count` is intentionally `0` — this is a solo project, so the senior-dev review pass substitutes for a second human approver rather than blocking merge on one.
- **Milestones/Issues/Project board**: GitHub Milestones M1–M5 mirror the plan's milestone breakdown (M1 is closed). Each milestone has one tracking issue (#1–#5) summarizing its scope from the plan. All issues are on the "AddressRefine Roadmap" project board. When a milestone's scope changes, update its issue body and milestone description, not just this file.
- **CI status checks are not yet required** on the branch protection rule because `.github/workflows/ci.yml` doesn't exist until M5. Once M5 lands CI, add it as a required status check on `main`.
