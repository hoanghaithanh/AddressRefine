"""Column-mapping step: GET/POST "/mapping"."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.compute import get_compute_backend
from app.deps import get_session
from app.models.domain import ColumnMapping, Session
from app.models.schemas import MappingForm

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _best_guess_mapping(headers: list[str]) -> ColumnMapping:
    """Guess a ColumnMapping from header names via case-insensitive substring match.

    For each logical field, picks the first header containing the relevant
    substring(s); None/empty street default if nothing matches (the template
    will simply show no pre-selected option in that case).
    """

    def find(*substrings: str) -> str | None:
        for header in headers:
            lowered = header.lower()
            if any(sub in lowered for sub in substrings):
                return header
        return None

    return ColumnMapping(
        street_col=find("street", "address") or "",
        zip_col=find("zip"),
        city_col=find("city"),
        country_col=find("country"),
    )


@router.get("/mapping")
async def mapping_form(request: Request, session: Session = Depends(get_session)):
    """Render the mapping page, redirecting to upload if there's no dataset yet."""
    frame = session.current_df
    if frame is None:
        return RedirectResponse(url="/", status_code=303)

    backend = get_compute_backend()
    headers = backend.get_headers(frame)

    # Only auto-guess if the user hasn't already chosen/confirmed a mapping,
    # so navigating back doesn't clobber their prior selection.
    mapping = session.mapping or _best_guess_mapping(headers)

    return templates.TemplateResponse(
        request,
        "mapping.html",
        {"headers": headers, "mapping": mapping, "active_step": "mapping"},
    )


@router.post("/mapping")
async def mapping_submit(
    request: Request,
    street_col: str = Form(...),
    zip_col: str | None = Form(None),
    city_col: str | None = Form(None),
    country_col: str | None = Form(None),
    session: Session = Depends(get_session),
):
    """Validate and save the submitted column mapping."""
    frame = session.current_df
    if frame is None:
        return RedirectResponse(url="/", status_code=303)

    backend = get_compute_backend()
    headers = backend.get_headers(frame)

    # Treat blank "-- none --" selections as None before validation.
    zip_col = zip_col or None
    city_col = city_col or None
    country_col = country_col or None

    def _rerender_with_error(message: str):
        submitted = ColumnMapping(street_col, zip_col, city_col, country_col)
        return templates.TemplateResponse(
            request,
            "mapping.html",
            {
                "headers": headers,
                "mapping": submitted,
                "active_step": "mapping",
                "flash": {"level": "error", "message": message},
            },
            status_code=422,
        )

    try:
        form = MappingForm(
            street_col=street_col,
            zip_col=zip_col,
            city_col=city_col,
            country_col=country_col,
        )
    except ValidationError as exc:
        return _rerender_with_error("; ".join(error["msg"] for error in exc.errors()))

    # Every mapped column (not just street_col) must be a real CSV header,
    # otherwise a later extract_columns() call would KeyError on a bogus name.
    for col in (form.street_col, form.zip_col, form.city_col, form.country_col):
        if col is not None and col not in headers:
            return _rerender_with_error(f"'{col}' is not a column in the uploaded CSV.")

    session.mapping = ColumnMapping(
        street_col=form.street_col,
        zip_col=form.zip_col,
        city_col=form.city_col,
        country_col=form.country_col,
    )

    return RedirectResponse(url="/algorithm", status_code=303)
