"""Tests for app/routers/results.py."""

from __future__ import annotations

from tests.conftest import sample_csv_bytes


def _upload_and_map(client, *, street_col: str = "StreetAddress", zip_col: str = "ZipCode"):
    client.post(
        "/upload",
        files={"file": ("addresses.csv", sample_csv_bytes(), "text/csv")},
        follow_redirects=False,
    )
    return client.post(
        "/mapping",
        data={"street_col": street_col, "zip_col": zip_col},
        follow_redirects=False,
    )


def _upload_csv_with_duplicates(client):
    """Upload a CSV where two rows fingerprint-match (case/punctuation only diff)."""
    csv_bytes = b"StreetAddress,ZipCode\n123 Main St,00501\n123 MAIN ST.,00501\n456 Oak Ave,NA\n"
    client.post(
        "/upload",
        files={"file": ("addresses.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )
    return client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode"},
        follow_redirects=False,
    )


def test_get_results_without_mapping_redirects_to_mapping(client):
    response = client.get("/results", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"


def test_get_results_without_algorithm_redirects_to_algorithm(client):
    """AC-M2-22: a confirmed mapping but no algorithm run yet -> redirect to /algorithm."""
    _upload_and_map(client)

    response = client.get("/results", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/algorithm"


def test_get_results_renders_groups_readonly(client):
    """AC-M2-21: candidate_pairs populated -> 200, each group's row addresses rendered."""
    _upload_csv_with_duplicates(client)
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)

    response = client.get("/results")

    assert response.status_code == 200
    text = response.text
    assert "123 Main St" in text
    assert "123 MAIN ST." in text
    assert "results-table" in text
    # Accept/Reject controls present but inert (disabled).
    assert "disabled" in text


def test_get_results_distance_column_blank_for_key_collision(client):
    """AC-M2-21a: distance column renders blank (em dash placeholder) for
    key-collision algorithms, where pair.distance is None."""
    _upload_csv_with_duplicates(client)
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)

    response = client.get("/results")

    assert response.status_code == 200
    assert "pair-row-distance" in response.text
    assert "&mdash;" in response.text


def test_get_results_empty_state_suggests_next_action(client):
    """AC-M2-26: zero clusters -> distinguishable empty-state element with an
    actionable message, not a bare empty table."""
    _upload_and_map(client)
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)

    response = client.get("/results")

    assert response.status_code == 200
    text = response.text
    assert "results-empty-state" in text
    assert "no candidate duplicates" in text.lower()
    assert "different algorithm" in text.lower() or "adjust its parameters" in text.lower()
    assert "results-table" not in text


def test_get_results_no_post_handler_exists(client):
    """AC-M2-21: there is no working POST /results/* handler in M2."""
    _upload_csv_with_duplicates(client)
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)

    response = client.post("/results", data={}, follow_redirects=False)

    assert response.status_code in (404, 405)

    # candidate_pairs must be unaffected by the failed POST.
    get_after = client.get("/results")
    assert get_after.status_code == 200
    assert "123 Main St" in get_after.text


def test_post_results_accept_subpath_404s(client):
    """No working POST /results/<id>/accept-style route exists either."""
    _upload_csv_with_duplicates(client)
    client.post("/algorithm", data={"algorithm_key": "fingerprint"}, follow_redirects=False)

    response = client.post("/results/0/accept", data={}, follow_redirects=False)

    assert response.status_code == 404
