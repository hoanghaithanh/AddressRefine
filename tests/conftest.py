"""Shared pytest fixtures for the AddressRefine test suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.session import session_store


@pytest.fixture(autouse=True)
def _clear_sessions():
    """Reset the process-wide session store before/after every test.

    `session_store` is a module-level singleton, so without this, sessions
    created by one test (and the cookies pointing at them) could otherwise
    leak state into a later test.
    """
    session_store.clear()
    yield
    session_store.clear()


@pytest.fixture
def client():
    """A TestClient with its own cookie jar, backed by a clean session store."""
    return TestClient(app)


def sample_csv_bytes() -> bytes:
    """CSV bytes with headers matchable to street/zip/city/country, plus data rows."""
    return (
        b"ZipCode,StreetAddress,City,Country\n"
        b"00501,123 Main St,Springfield,USA\n"
        b"NA,456 Oak Ave,Shelbyville,USA\n"
    )


@pytest.fixture
def sample_csv():
    """Fixture wrapper around `sample_csv_bytes` for tests that prefer a fixture."""
    return sample_csv_bytes()
