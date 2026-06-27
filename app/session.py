"""In-memory session storage.

No database in v1 — sessions live in a process-local dict for the lifetime of
the server. This is fine since the spec calls for a single session at a time.
"""

from __future__ import annotations

from uuid import uuid4

from app.models.domain import Session


class SessionStore:
    """Process-wide in-memory store of `Session` objects keyed by session id."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get(self, session_id: str) -> Session | None:
        """Return the session for `session_id`, or None if it doesn't exist."""
        return self._sessions.get(session_id)

    def create(self) -> Session:
        """Create a brand-new session with a fresh uuid4 id, store, and return it."""
        session_id = str(uuid4())
        session = Session(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def get_or_create(self, session_id: str | None) -> Session:
        """Return the existing session for `session_id` if present, otherwise create one.

        Also used when `session_id` is None (e.g. no cookie was sent yet).
        """
        if session_id is not None:
            existing = self._sessions.get(session_id)
            if existing is not None:
                return existing
        return self.create()

    def clear(self) -> None:
        """Drop all stored sessions. Intended for test isolation between cases."""
        self._sessions.clear()


# Single process-wide store instance, shared by the `get_session` dependency.
session_store = SessionStore()
