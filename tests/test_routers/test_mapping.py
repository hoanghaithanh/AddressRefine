"""Tests for app/routers/mapping.py."""

from __future__ import annotations

from tests.conftest import sample_csv_bytes


def _upload_sample(client):
    return client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )


def test_get_mapping_without_upload_redirects_to_root(client):
    response = client.get("/mapping", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_get_mapping_after_upload_shows_headers_with_best_guess_selected(client):
    _upload_sample(client)

    response = client.get("/mapping")

    assert response.status_code == 200
    text = response.text
    for header in ["ZipCode", "StreetAddress", "City", "Country"]:
        assert header in text

    # Best-guess: header containing "street"/"address" -> StreetAddress, etc.
    assert '<option value="StreetAddress" selected>' in text
    assert '<option value="ZipCode" selected>' in text
    assert '<option value="City" selected>' in text
    assert '<option value="Country" selected>' in text


def test_post_mapping_valid_redirects(client):
    _upload_sample(client)

    response = client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"


def test_post_mapping_street_col_not_a_real_header_returns_422(client):
    _upload_sample(client)

    response = client.post(
        "/mapping",
        data={"street_col": "NotAHeader", "zip_col": "ZipCode"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "not a column" in response.text.lower()


def test_post_mapping_zip_col_not_a_real_header_returns_422(client):
    _upload_sample(client)

    response = client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "NotAHeader"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "not a column" in response.text.lower()


def test_post_mapping_without_zip_or_city_returns_422(client):
    _upload_sample(client)

    response = client.post(
        "/mapping",
        data={"street_col": "StreetAddress"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_post_mapping_then_get_shows_chosen_mapping_not_best_guess(client):
    _upload_sample(client)

    # Deliberately choose a mapping different from the best-guess pre-fill:
    # map "City" as the street column, and only set city_col (no zip_col),
    # so we can tell the GET page reflects this exact submission afterwards.
    client.post(
        "/mapping",
        data={"street_col": "City", "city_col": "City"},
        follow_redirects=False,
    )

    response = client.get("/mapping")

    assert response.status_code == 200
    text = response.text
    # The street select should now have "City" selected, not "StreetAddress".
    assert '<option value="City" selected>' in text
    assert '<option value="StreetAddress" selected>' not in text
