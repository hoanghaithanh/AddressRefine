"""Algorithm-selection step: GET/POST "/algorithm"."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.algorithms.base import AlgorithmFamily
from app.algorithms.registry import list_algorithms
from app.deps import get_session
from app.models.domain import Session
from app.services.matching_service import run_matching

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/algorithm")
async def algorithm_form(request: Request, session: Session = Depends(get_session)):
    """Render the algorithm-selection page, redirecting to /mapping if unconfirmed."""
    if session.mapping is None:
        return RedirectResponse(url="/mapping", status_code=303)

    return templates.TemplateResponse(
        request,
        "algorithm.html",
        {
            "algorithms": list_algorithms(),
            "selected_key": session.algorithm_key,
            "algorithm_params": session.algorithm_params,
            "active_step": "algorithm",
            "AlgorithmFamily": AlgorithmFamily,
        },
    )


@router.post("/algorithm")
async def algorithm_submit(
    request: Request,
    algorithm_key: str = Form(...),
    n: str | None = Form(None),
    threshold: str | None = Form(None),
    session: Session = Depends(get_session),
):
    """Validate and persist the chosen algorithm + params, then run matching."""
    if session.mapping is None:
        return RedirectResponse(url="/mapping", status_code=303)

    algorithms = list_algorithms()
    algorithms_by_key = {algo.key: algo for algo in algorithms}

    def _rerender_with_error(message: str):
        return templates.TemplateResponse(
            request,
            "algorithm.html",
            {
                "algorithms": algorithms,
                "selected_key": algorithm_key,
                "algorithm_params": {
                    **({"n": n} if n is not None else {}),
                    **({"threshold": threshold} if threshold is not None else {}),
                },
                "active_step": "algorithm",
                "flash": {"level": "error", "message": message},
                "AlgorithmFamily": AlgorithmFamily,
            },
            status_code=422,
        )

    if algorithm_key not in algorithms_by_key:
        return _rerender_with_error(f"'{algorithm_key}' is not a known algorithm.")

    params: dict[str, object] = {}

    if algorithm_key == "ngram_fingerprint":
        # n must be a positive integer; reject anything else (including
        # floats like "2.5") with a 422 + flash, without persisting it or
        # running matching.
        if n is None or n.strip() == "":
            n_value: int | None = 2
        else:
            try:
                n_value = int(n)
            except ValueError:
                return _rerender_with_error("'n' must be a positive integer.")
        if n_value is None or n_value <= 0:
            return _rerender_with_error("'n' must be a positive integer.")
        params["n"] = n_value

    elif algorithm_key == "levenshtein":
        # threshold must be a non-negative integer (0 is valid).
        if threshold is None or threshold.strip() == "":
            threshold_value: int = 3  # use default
        else:
            try:
                threshold_value = int(threshold)
            except ValueError:
                return _rerender_with_error(
                    "'threshold' must be a non-negative integer for Levenshtein."
                )
        if threshold_value < 0:
            return _rerender_with_error(
                "'threshold' must be a non-negative integer for Levenshtein."
            )
        params["threshold"] = threshold_value

    elif algorithm_key == "ncd":
        # threshold must be an integer in [1, 10].
        if threshold is None or threshold.strip() == "":
            threshold_value = 3  # use default
        else:
            try:
                threshold_value = int(threshold)
            except ValueError:
                return _rerender_with_error(
                    "'threshold' must be an integer between 1 and 10 for NCD."
                )
        if threshold_value < 1 or threshold_value > 10:
            return _rerender_with_error("'threshold' must be an integer between 1 and 10 for NCD.")
        params["threshold"] = threshold_value

    # Key-collision algorithms (fingerprint, ngram_fingerprint) ignore any
    # threshold value — no validation is applied.

    session.algorithm_key = algorithm_key
    session.algorithm_params = params
    run_matching(session)

    return RedirectResponse(url="/results", status_code=303)
