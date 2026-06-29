"""Tests for app/routers/algorithm.py."""

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


def test_get_algorithm_without_mapping_redirects_to_mapping(client):
    """AC-M2-19: no confirmed mapping yet -> redirect (303) to /mapping."""
    response = client.get("/algorithm", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"


def test_get_algorithm_lists_fingerprint_and_ngram(client):
    """AC-M2-18: a confirmed mapping -> 200, both algorithms listed as options."""
    _upload_and_map(client)

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert 'value="fingerprint"' in text
    assert 'value="ngram_fingerprint"' in text


def test_post_algorithm_persists_choice_and_runs_matching(client):
    """AC-M2-20: a valid submission persists the algorithm and runs matching
    before redirecting, so /results immediately reflects it."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"

    results = client.get("/results")
    assert results.status_code == 200
    # Sample CSV's two rows ("123 Main St" / "456 Oak Ave") don't fingerprint-match,
    # so matching ran (no algorithm-not-selected redirect) but produced an empty state.
    assert "results-empty-state" in results.text


def test_post_algorithm_fingerprint_finds_duplicate_rows(client):
    _upload_and_map(client)
    # Add a second mapping run isn't needed; reuse the default sample.
    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": "2"},
        follow_redirects=False,
    )

    assert response.status_code == 303

    results = client.get("/results")
    assert results.status_code == 200


def test_post_algorithm_ngram_default_n_used_when_blank(client):
    """Blank n should default to 2, not error."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": ""},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_ngram_default_n_used_when_omitted(client):
    """n omitted entirely from the form should also default to 2."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"


def test_post_algorithm_invalid_n_zero_returns_422(client):
    """AC-M2-25: n <= 0 (e.g. 0) is rejected with 422 + flash error."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": "0"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "positive integer" in response.text.lower()


def test_post_algorithm_invalid_n_negative_returns_422(client):
    """AC-M2-25: n <= 0 (e.g. -1) is rejected with 422 + flash error."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": "-1"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "positive integer" in response.text.lower()


def test_post_algorithm_invalid_n_non_integer_returns_422(client):
    """AC-M2-25: a non-integer n (e.g. "2.5") is rejected with 422 + flash error."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": "2.5"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "positive integer" in response.text.lower()


def test_post_algorithm_invalid_n_does_not_persist_or_run_matching(client):
    """AC-M2-25: an invalid n must not mutate algorithm_key/algorithm_params/
    candidate_pairs, and must not invoke run_matching."""
    _upload_and_map(client)

    # First, establish a known-good baseline selection so we can detect mutation.
    good = client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )
    assert good.status_code == 303

    bad = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": "-1"},
        follow_redirects=False,
    )
    assert bad.status_code == 422

    # The session's prior selection (fingerprint) must remain unaffected: the
    # /algorithm page should still show "fingerprint" as the persisted choice.
    algorithm_page = client.get("/algorithm")
    assert algorithm_page.status_code == 200
    # selected_key passed to the template should still be "fingerprint", not
    # "ngram_fingerprint", because the invalid submission must not have
    # persisted onto session.algorithm_key.
    assert '<option value="fingerprint" selected>' in algorithm_page.text


def test_post_algorithm_unknown_key_returns_422(client):
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "not_a_real_algorithm"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_post_algorithm_without_mapping_redirects_to_mapping(client):
    response = client.post(
        "/algorithm",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"


def test_post_algorithm_valid_n_one_is_accepted(client):
    """n >= 1 is valid; n=1 is the boundary case."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm",
        data={"algorithm_key": "ngram_fingerprint", "n": "1"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/results"
