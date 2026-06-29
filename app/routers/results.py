"""Results step: GET "/results" — read-only candidate-group review.

No working `POST /results/*` handler exists in M2: accept/reject controls
may appear in markup but are inert (no route to receive them).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.compute import get_compute_backend
from app.deps import get_session
from app.models.domain import Session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/results")
async def results_view(request: Request, session: Session = Depends(get_session)):
    """Render candidate groups read-only, redirecting to /algorithm if no run yet."""
    if session.mapping is None:
        return RedirectResponse(url="/mapping", status_code=303)

    if session.algorithm_key is None:
        return RedirectResponse(url="/algorithm", status_code=303)

    frame = session.current_df
    backend = get_compute_backend()
    columns_by_row = backend.extract_columns(frame, session.mapping) if frame is not None else {}

    groups = [
        {
            "row_indices": pair.row_indices,
            "distance": pair.distance,
            "rows": [
                {"row_index": idx, "columns": columns_by_row.get(idx, {})}
                for idx in pair.row_indices
            ],
        }
        for pair in session.candidate_pairs
    ]

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "groups": groups,
            "algorithm_key": session.algorithm_key,
            "active_step": "results",
        },
    )
