"""Combined Method/Distance-function/parameter selection + live results table.

`GET /algorithm` renders the page; `POST /algorithm/recompute` is the
HTMX-triggered live-recompute endpoint that re-validates and persists the
chosen algorithm + params, reruns matching, and returns only the refreshed
results-table partial. `POST /merge` applies a batch merge of checked rows
and also returns a refreshed results-table partial.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.algorithms.base import AlgorithmFamily
from app.algorithms.registry import list_algorithms
from app.compute import get_compute_backend
from app.deps import get_session
from app.models.domain import Session
from app.services.matching_service import run_matching
from app.services.merge_service import MergeConflictError, MergeRequestRow, apply_merge

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _results_table_context(request: Request, session: Session) -> dict:
    """Build the template context for the results-table partial."""
    frame = session.current_df
    backend = get_compute_backend()
    columns_by_row = backend.extract_columns(frame, session.mapping) if frame is not None else {}

    algorithm = None
    if session.algorithm_key is not None:
        algorithm = next(
            (algo for algo in list_algorithms() if algo.key == session.algorithm_key), None
        )

    groups = [
        {
            "pair_id": pair.pair_id,
            "row_indices": pair.row_indices,
            "distance": pair.distance,
            "rows": [
                {"row_index": idx, "columns": columns_by_row.get(idx, {})}
                for idx in pair.row_indices
            ],
        }
        for pair in session.candidate_pairs
    ]

    return {
        "request": request,
        "groups": groups,
        "algorithm_key": session.algorithm_key,
        "algorithm_family": algorithm.family if algorithm is not None else None,
        "AlgorithmFamily": AlgorithmFamily,
    }


def _validate_params(algorithm_key: str, n: str | None, threshold: str | None):
    """Validate and coerce submitted params for `algorithm_key`.

    Returns `(params, error_message)`; exactly one of the two is non-`None`/
    non-empty (params is `{}` and error_message is `None` on success for
    algorithms with no params).
    """
    params: dict[str, object] = {}

    if algorithm_key == "ngram_fingerprint":
        if n is None or n.strip() == "":
            n_value: int | None = 2
        else:
            try:
                n_value = int(n)
            except ValueError:
                return None, "'n' must be a positive integer."
        if n_value is None or n_value <= 0:
            return None, "'n' must be a positive integer."
        params["n"] = n_value

    elif algorithm_key == "levenshtein":
        if threshold is None or threshold.strip() == "":
            threshold_value: int = 3
        else:
            try:
                threshold_value = int(threshold)
            except ValueError:
                return None, "'threshold' must be a non-negative integer for Levenshtein."
        if threshold_value < 0:
            return None, "'threshold' must be a non-negative integer for Levenshtein."
        params["threshold"] = threshold_value

    elif algorithm_key == "ncd":
        if threshold is None or threshold.strip() == "":
            threshold_value = 3
        else:
            try:
                threshold_value = int(threshold)
            except ValueError:
                return None, "'threshold' must be an integer between 1 and 10 for NCD."
        if threshold_value < 1 or threshold_value > 10:
            return None, "'threshold' must be an integer between 1 and 10 for NCD."
        params["threshold"] = threshold_value

    # Fingerprint (plain) ignores any n/threshold value — no validation applied.

    return params, None


@router.get("/algorithm")
async def algorithm_form(request: Request, session: Session = Depends(get_session)):
    """Render the combined Method/Distance-function/results page.

    Redirects to /mapping if no mapping has been confirmed yet. If no
    algorithm has been selected yet, defaults to the first registered
    algorithm and runs matching immediately so the page loads pre-populated.
    """
    if session.mapping is None:
        return RedirectResponse(url="/mapping", status_code=303)

    algorithms = list_algorithms()

    if session.algorithm_key is None:
        default_algorithm = algorithms[0]
        session.algorithm_key = default_algorithm.key
        session.algorithm_params = {
            spec.name: spec.default for spec in default_algorithm.param_specs
        }
        run_matching(session)

    selected_algorithm = next(
        (algo for algo in algorithms if algo.key == session.algorithm_key), None
    )

    context = {
        "algorithms": algorithms,
        "selected_key": session.algorithm_key,
        "selected_algorithm": selected_algorithm,
        "algorithm_params": session.algorithm_params,
        "active_step": "algorithm",
        "AlgorithmFamily": AlgorithmFamily,
        **_results_table_context(request, session),
    }

    return templates.TemplateResponse(request, "algorithm.html", context)


@router.post("/algorithm/recompute")
async def algorithm_recompute(
    request: Request,
    algorithm_key: str | None = Form(None),
    n: str | None = Form(None),
    threshold: str | None = Form(None),
    session: Session = Depends(get_session),
):
    """HTMX live-recompute: validate + persist algorithm/params, rerun matching.

    Returns only the re-rendered results-table partial. Invalid params return
    HTTP 422 with a flash error, without updating `session.algorithm_key`/
    `algorithm_params` or invoking `run_matching`.
    """
    if session.mapping is None:
        return RedirectResponse(url="/mapping", status_code=303)

    if algorithm_key is None or algorithm_key.strip() == "":
        return templates.TemplateResponse(
            request,
            "partials/_results_table.html",
            {
                **_results_table_context(request, session),
                "flash": {
                    "level": "error",
                    "message": "algorithm_key is required.",
                },
            },
            status_code=422,
        )

    algorithms_by_key = {algo.key: algo for algo in list_algorithms()}

    if algorithm_key not in algorithms_by_key:
        return templates.TemplateResponse(
            request,
            "partials/_results_table.html",
            {
                **_results_table_context(request, session),
                "flash": {
                    "level": "error",
                    "message": f"'{algorithm_key}' is not a known algorithm.",
                },
            },
            status_code=422,
        )

    params, error_message = _validate_params(algorithm_key, n, threshold)

    if error_message is not None:
        return templates.TemplateResponse(
            request,
            "partials/_results_table.html",
            {
                **_results_table_context(request, session),
                "flash": {"level": "error", "message": error_message},
            },
            status_code=422,
        )

    session.algorithm_key = algorithm_key
    session.algorithm_params = params
    run_matching(session)

    return templates.TemplateResponse(
        request, "partials/_results_table.html", _results_table_context(request, session)
    )


@router.post("/merge")
async def merge_submit(request: Request, session: Session = Depends(get_session)):
    """Apply a batch merge of checked rows, then return a refreshed results table.

    Parses repeated `pair_id`/`new_value` form fields (one pair per checked
    row) submitted by `merge-form` in `partials/_results_table.html`. On a
    conflict, returns a flash error without mutating session state.
    """
    if session.mapping is None:
        return RedirectResponse(url="/mapping", status_code=303)

    form = await request.form()
    pair_ids = form.getlist("pair_id")
    new_values = form.getlist("new_value")

    merge_requests = [
        MergeRequestRow(pair_id=pair_id, new_value=new_value)
        for pair_id, new_value in zip(pair_ids, new_values)
    ]

    backend = get_compute_backend()

    try:
        apply_merge(session, backend, merge_requests)
    except MergeConflictError as exc:
        details = "; ".join(
            f"row {row_index} -> {values}" for row_index, values in sorted(exc.conflicts.items())
        )
        return templates.TemplateResponse(
            request,
            "partials/_results_table.html",
            {
                **_results_table_context(request, session),
                "flash": {
                    "level": "error",
                    "message": f"Merge blocked: conflicting target values ({details}).",
                },
            },
            status_code=422,
        )

    return templates.TemplateResponse(
        request, "partials/_results_table.html", _results_table_context(request, session)
    )


@router.get("/results")
async def results_redirect():
    """Legacy/bookmarked-URL redirect: the standalone results page no longer exists."""
    return RedirectResponse(url="/algorithm", status_code=303)
