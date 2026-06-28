"""Algorithm-selection step: GET/POST "/algorithm"."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

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
        },
    )


@router.post("/algorithm")
async def algorithm_submit(
    request: Request,
    algorithm_key: str = Form(...),
    n: str | None = Form(None),
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
                "algorithm_params": {"n": n} if n is not None else {},
                "active_step": "algorithm",
                "flash": {"level": "error", "message": message},
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

    session.algorithm_key = algorithm_key
    session.algorithm_params = params
    run_matching(session)

    return RedirectResponse(url="/results", status_code=303)
