"""FastAPI dependencies shared across routers."""

from __future__ import annotations

from fastapi import Request, Response

from app.config import settings
from app.models.domain import Session
from app.session import session_store


def get_session(request: Request, response: Response) -> Session:
    """Resolve the current session from the session cookie, creating one if needed.

    Reads `settings.SESSION_COOKIE_NAME` from the incoming request cookies. If
    it's missing or doesn't match a known session, a new session is created
    (uuid4 id) and the cookie is (re-)set, httponly.

    Note: most routes in this app return a `Response` object directly
    (`TemplateResponse`/`RedirectResponse`) rather than plain data. FastAPI
    only merges headers set on this injected `response` into the final
    response when the endpoint returns non-`Response` data -- when an
    endpoint returns a `Response` directly, that returned object is used
    as-is and headers set here would otherwise be silently dropped. To
    handle both cases, the new cookie is also stashed on `request.state`,
    and `SessionCookieMiddleware` (see app.main) applies it to whatever
    response object actually gets sent.
    """
    cookie_session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    session = session_store.get_or_create(cookie_session_id)

    if cookie_session_id != session.session_id:
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session.session_id,
            httponly=True,
            samesite="lax",
        )
        request.state.new_session_id = session.session_id

    return session
