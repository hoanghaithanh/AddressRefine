"""Application settings.

Plain class (not pydantic BaseSettings) since the `pydantic-settings` package
is not part of this project's dependencies. Values can still be overridden
via environment variables if needed later; for now they are static defaults.
"""

from __future__ import annotations


class Settings:
    """Static application configuration for AddressRefine."""

    SESSION_COOKIE_NAME: str = "addressrefine_session"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB limit per the spec


settings = Settings()
