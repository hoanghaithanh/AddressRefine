"""Tests for app/routers/upload.py."""

from __future__ import annotations

from app.config import settings
from tests.conftest import sample_csv_bytes


def test_get_upload_form_returns_200_with_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "form" in response.text
    assert 'action="/upload"' in response.text


def test_post_upload_valid_csv_redirects_to_mapping_and_sets_cookie(client):
    response = client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"
    assert settings.SESSION_COOKIE_NAME in response.cookies


def test_post_upload_oversized_file_does_not_redirect(client):
    oversized = b"a" * (settings.MAX_UPLOAD_BYTES + 1)

    response = client.post(
        "/upload",
        files={"file": ("big.csv", oversized, "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "too large" in response.text.lower()


def test_post_upload_garbage_empty_csv_returns_400(client):
    response = client.post(
        "/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "flash" in response.text.lower() or "error" in response.text.lower()
