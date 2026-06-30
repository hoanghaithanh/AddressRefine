"""Tests for app/routers/algorithm.py — M3 threshold validation extensions.

Covers AC-M3-31 through AC-M3-37.
"""

from __future__ import annotations

from tests.conftest import sample_csv_bytes


def _upload_and_map(client, *, zip_col: str = "ZipCode", city_col: str | None = None):
    """Upload the shared sample CSV and confirm a mapping with zip+optional city."""
    client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )
    data: dict = {"street_col": "StreetAddress", "zip_col": zip_col}
    if city_col:
        data["city_col"] = city_col
    return client.post(
        "/mapping",
        data=data,
        follow_redirects=False,
    )


def _upload_and_map_with_duplicates(client):
    """Upload a CSV with duplicate rows so levenshtein/ncd actually finds matches."""
    csv_bytes = (
        b"StreetAddress,ZipCode,City\n"
        b"123 Main St,00501,Springfield\n"
        b"123 Main Street,00501,Springfield\n"
        b"456 Oak Ave,00502,Shelbyville\n"
    )
    client.post(
        "/upload",
        files={"file": ("addresses.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )
    return client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode", "city_col": "City"},
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# AC-M3-31 — POST /algorithm accepts Levenshtein threshold >= 0
# ---------------------------------------------------------------------------


def test_post_algorithm_levenshtein_threshold_zero_accepted(client):
    """AC-M3-31: threshold=0 is valid for Levenshtein (boundary case)."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "0"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_levenshtein_threshold_1_accepted(client):
    """AC-M3-31: threshold=1 is valid for Levenshtein."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "1"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_levenshtein_default_threshold_accepted(client):
    """AC-M3-31: Levenshtein with no threshold uses default=3."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": ""},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_levenshtein_threshold_10_accepted(client):
    """AC-M3-31: large threshold values are valid for Levenshtein."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "10"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_levenshtein_persists_algorithm_key_and_params(client):
    """AC-M3-31: on success, session.algorithm_key='levenshtein' and params has threshold."""
    _upload_and_map_with_duplicates(client)

    client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "5"},
        follow_redirects=False,
    )

    # The /algorithm GET page should show 'levenshtein' as selected.
    page = client.get("/algorithm")
    assert page.status_code == 200
    assert 'value="levenshtein" selected' in page.text


# ---------------------------------------------------------------------------
# AC-M3-32 — POST /algorithm rejects invalid Levenshtein threshold
# ---------------------------------------------------------------------------


def test_post_algorithm_levenshtein_negative_threshold_returns_422(client):
    """AC-M3-32: threshold=-1 is rejected with 422 + flash."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "-1"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "threshold" in response.text.lower()


def test_post_algorithm_levenshtein_non_integer_threshold_returns_422(client):
    """AC-M3-32: threshold='2.5' is rejected with 422 + flash."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "2.5"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "threshold" in response.text.lower()


def test_post_algorithm_levenshtein_alphabetic_threshold_returns_422(client):
    """AC-M3-32: threshold='abc' is rejected with 422 + flash."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "abc"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_post_algorithm_levenshtein_invalid_does_not_persist(client):
    """AC-M3-32: invalid threshold must not mutate session.algorithm_key or params."""
    _upload_and_map_with_duplicates(client)

    # Establish a clean baseline selection first.
    client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    # Submit an invalid levenshtein threshold.
    bad = client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "-5"},
        follow_redirects=False,
    )
    assert bad.status_code == 422

    # Session must still show 'fingerprint' as the persisted algorithm.
    page = client.get("/algorithm")
    assert 'value="fingerprint" selected' in page.text


# ---------------------------------------------------------------------------
# AC-M3-33 — POST /algorithm accepts NCD threshold in range [1, 10]
# ---------------------------------------------------------------------------


def test_post_algorithm_ncd_threshold_1_accepted(client):
    """AC-M3-33: threshold=1 is the lower bound for NCD."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "1"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_ncd_threshold_3_accepted(client):
    """AC-M3-33: threshold=3 (default) is valid for NCD."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "3"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_ncd_threshold_10_accepted(client):
    """AC-M3-33: threshold=10 is the upper bound for NCD."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "10"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_ncd_persists_algorithm_key_and_params(client):
    """AC-M3-33: on success, session reflects ncd key and threshold param."""
    _upload_and_map_with_duplicates(client)

    client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "5"},
        follow_redirects=False,
    )

    page = client.get("/algorithm")
    assert page.status_code == 200
    assert 'value="ncd" selected' in page.text


# ---------------------------------------------------------------------------
# AC-M3-34 — POST /algorithm rejects NCD threshold=0
# ---------------------------------------------------------------------------


def test_post_algorithm_ncd_threshold_zero_returns_422(client):
    """AC-M3-34: threshold=0 is rejected for NCD with 422 + flash."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "0"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "threshold" in response.text.lower()


def test_post_algorithm_ncd_threshold_zero_does_not_run_matching(client):
    """AC-M3-34: run_matching must not be invoked when threshold=0 for NCD."""
    _upload_and_map_with_duplicates(client)

    # Set a known prior state.
    client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "0"},
        follow_redirects=False,
    )

    # Algorithm key must remain 'fingerprint' — ncd with invalid threshold didn't persist.
    page = client.get("/algorithm")
    assert 'value="fingerprint" selected' in page.text


# ---------------------------------------------------------------------------
# AC-M3-35 — POST /algorithm rejects NCD threshold > 10
# ---------------------------------------------------------------------------


def test_post_algorithm_ncd_threshold_11_returns_422(client):
    """AC-M3-35: threshold=11 is rejected for NCD with 422 + flash."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "11"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "threshold" in response.text.lower()


def test_post_algorithm_ncd_threshold_100_returns_422(client):
    """AC-M3-35: threshold=100 is rejected for NCD."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "100"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_post_algorithm_ncd_threshold_non_integer_returns_422(client):
    """AC-M3-35: non-integer threshold is rejected for NCD."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ncd", "threshold": "3.5"},
        follow_redirects=False,
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# AC-M3-36 — POST /algorithm ignores threshold for key-collision algorithms
# ---------------------------------------------------------------------------


def test_post_algorithm_fingerprint_ignores_threshold(client):
    """AC-M3-36: fingerprint algorithm accepts any threshold value without validation."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint", "threshold": "999"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_fingerprint_ignores_negative_threshold(client):
    """AC-M3-36: fingerprint algorithm accepts negative threshold without error."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint", "threshold": "-99"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_ngram_ignores_threshold_validation(client):
    """AC-M3-36: ngram_fingerprint algorithm ignores threshold entirely."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": "2", "threshold": "-5"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


# ---------------------------------------------------------------------------
# AC-M3-37 — GET /algorithm renders threshold field for NN algorithms
# ---------------------------------------------------------------------------


def test_get_algorithm_page_contains_threshold_input_field(client):
    """AC-M3-37: algorithm.html renders a threshold input field (present in HTML)."""
    _upload_and_map(client)

    response = client.get("/algorithm")

    assert response.status_code == 200
    assert 'name="threshold"' in response.text


def test_get_algorithm_page_threshold_shown_when_levenshtein_selected(client):
    """AC-M3-37: threshold visible field (not hidden) when Levenshtein is selected."""
    _upload_and_map_with_duplicates(client)
    # Select levenshtein so it becomes the session's algorithm.
    client.post(
        "/algorithm",
        data={"algorithm_key": "levenshtein", "threshold": "3"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    # The threshold <input type="number"> should be present (not type="hidden")
    # when the selected algorithm is levenshtein.
    assert 'type="number"' in response.text
    assert 'name="threshold"' in response.text


def test_get_algorithm_page_threshold_hidden_for_key_collision(client):
    """AC-M3-37: threshold is a hidden field for key-collision algorithms."""
    _upload_and_map(client)
    client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    # For key-collision, the threshold field is type="hidden", not type="number".
    assert 'type="hidden"' in response.text
    assert 'name="threshold"' in response.text
