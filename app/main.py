"""FastAPI application factory for AddressRefine."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import algorithm, mapping, results, upload


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(title="AddressRefine")

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.middleware("http")
    async def session_cookie_middleware(request: Request, call_next):
        """Ensure a freshly-created session cookie reaches the client.

        `app.deps.get_session` sets the cookie on its dependency-injected
        `Response`, but most routes here return their own `Response`
        directly (TemplateResponse/RedirectResponse), which FastAPI does not
        merge headers into. As a fallback, `get_session` also stashes the new
        session id on `request.state.new_session_id`; this middleware applies
        it to whatever response object the route actually returned.
        """
        response = await call_next(request)
        new_session_id = getattr(request.state, "new_session_id", None)
        if new_session_id is not None:
            # Setting the same cookie name/value twice is harmless (the
            # browser just keeps the last one), so no need to guard against
            # it having already been set.
            response.set_cookie(
                key=settings.SESSION_COOKIE_NAME,
                value=new_session_id,
                httponly=True,
                samesite="lax",
            )
        return response

    app.include_router(upload.router)
    app.include_router(mapping.router)
    app.include_router(algorithm.router)
    app.include_router(results.router)

    return app


app = create_app()
