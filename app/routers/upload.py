"""Upload step: GET "/" shows the upload form, POST "/upload" handles the CSV."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.compute import get_compute_backend
from app.config import settings
from app.deps import get_session
from app.models.domain import DatasetVersion, Session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def upload_form(request: Request, session: Session = Depends(get_session)):
    """Render the upload page.

    Shown even if the session already has a current dataset — re-uploading
    always starts a fresh dataset for M1.
    """
    return templates.TemplateResponse(request, "upload.html", {"active_step": "upload"})


@router.post("/upload")
async def upload_csv(
    request: Request,
    file: UploadFile,
    session: Session = Depends(get_session),
):
    """Accept a CSV upload, parse it, and start a new dataset version on success."""
    # Read in chunks and bail out as soon as the limit is exceeded, instead of
    # buffering the whole file first -- caps memory use for oversized uploads.
    chunks = []
    total = 0
    too_large = False
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.MAX_UPLOAD_BYTES:
            too_large = True
            break
        chunks.append(chunk)

    if too_large:
        return templates.TemplateResponse(
            request,
            "upload.html",
            {
                "active_step": "upload",
                "flash": {
                    "level": "error",
                    "message": (
                        f"File is too large. Maximum allowed size is "
                        f"{settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
                    ),
                },
            },
            status_code=400,
        )

    data = b"".join(chunks)
    backend = get_compute_backend()
    try:
        frame = backend.load_csv(data)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "upload.html",
            {"active_step": "upload", "flash": {"level": "error", "message": str(exc)}},
            status_code=400,
        )

    session.versions = [DatasetVersion(version=1, df=frame, created_from_merge=False)]
    session.mapping = None
    session.original_filename = file.filename

    return RedirectResponse(url="/mapping", status_code=303)
