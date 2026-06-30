"""Tests for app/routers/algorithm.py — M4 combined algorithm/results page +
pairwise merge-review.

Covers AC-M4-1 through AC-M4-24 (page structure, live recompute, results
table rendering/interaction affordances, no per-pair accept/reject routes)
and AC-M4-32 through AC-M4-34 (POST /merge router behavior) from
`docs/ba/acceptance-criteria/m4-merge-review.md`.
"""

from __future__ import annotations

from app.main import app
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


def _upload_and_map_with_duplicates(client):
    """Upload a CSV where two rows fingerprint-match (case/punctuation diff
    only), suitable for both key-collision and NN algorithm testing."""
    csv_bytes = (
        b"StreetAddress,ZipCode,City\n"
        b"123 Main St,00501,Springfield\n"
        b"123 MAIN ST.,00501,Springfield\n"
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
# AC-M4-1 — Method field with exactly two options
# ---------------------------------------------------------------------------


def test_get_algorithm_renders_method_field_with_nn_and_fingerprint_options(client):
    _upload_and_map(client)

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert 'id="method"' in text
    assert 'value="nearest_neighbor"' in text
    assert 'value="key_collision"' in text
    assert "Nearest Neighbor" in text
    assert "Fingerprint" in text


def test_get_algorithm_without_mapping_redirects_to_mapping(client):
    response = client.get("/algorithm", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"


# ---------------------------------------------------------------------------
# AC-M4-2 — Distance function options filtered by selected Method
# ---------------------------------------------------------------------------


def test_get_algorithm_distance_function_options_present_for_all_four_algorithms(client):
    """All 4 algorithm options are present in the rendered <select> (client-side
    JS does the actual visibility filtering per AC-M4-2); each carries a
    data-family attribute the JS reads."""
    _upload_and_map(client)

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert 'value="levenshtein"' in text
    assert 'value="ncd"' in text
    assert 'value="fingerprint"' in text
    assert 'value="ngram_fingerprint"' in text
    assert 'data-family="nearest_neighbor"' in text
    assert 'data-family="key_collision"' in text


def test_get_algorithm_distance_function_labels_match_registry(client):
    _upload_and_map(client)

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert ">Levenshtein Distance<" in text
    assert ">PPM / NCD<" in text
    assert ">Fingerprint<" in text
    assert ">N-Gram Fingerprint<" in text


# ---------------------------------------------------------------------------
# AC-M4-3 — param field labeled "Radius" for Levenshtein/NCD
# ---------------------------------------------------------------------------


def test_get_algorithm_radius_label_shown_for_levenshtein(client):
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "levenshtein", "threshold": "3"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert ">Radius<" in text
    assert 'name="threshold"' in text


def test_get_algorithm_radius_label_shown_for_ncd(client):
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ncd", "threshold": "3"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert ">Radius<" in text
    assert 'name="threshold"' in text


# ---------------------------------------------------------------------------
# AC-M4-4 — no parameter field at all for plain Fingerprint
# ---------------------------------------------------------------------------


def test_get_algorithm_no_param_field_for_fingerprint(client):
    _upload_and_map(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert 'id="param-field"' not in text
    assert 'id="param-field-group"' not in text


# ---------------------------------------------------------------------------
# AC-M4-5 — param field labeled "N-Gram size" for N-Gram Fingerprint
# ---------------------------------------------------------------------------


def test_get_algorithm_ngram_size_label_shown_for_ngram_fingerprint(client):
    _upload_and_map(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ngram_fingerprint", "n": "2"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert ">N-Gram size<" in text
    assert 'name="n"' in text


def test_get_algorithm_default_algorithm_runs_matching_immediately(client):
    """GET /algorithm with no prior algorithm_key defaults to the first
    registered algorithm (fingerprint) and runs matching eagerly."""
    _upload_and_map(client)

    response = client.get("/algorithm")

    assert response.status_code == 200
    assert 'value="fingerprint"' in response.text
    assert "selected" in response.text


# ---------------------------------------------------------------------------
# AC-M4-6/7/8 — live recompute via POST /algorithm/recompute
# ---------------------------------------------------------------------------


def test_recompute_change_method_to_nn_reruns_with_default_nn_algorithm(client):
    """AC-M4-6: changing Method (here simulated as the form posting a NN
    algorithm key) reruns matching and returns only the results-table partial."""
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "levenshtein", "threshold": "3"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    text = response.text
    assert 'id="results-table-container"' in text
    # Returns ONLY the partial — no surrounding page chrome.
    assert "<html" not in text
    assert "Match & Merge" not in text


def test_recompute_change_distance_function_reruns_matching(client):
    """AC-M4-7: switching Distance function (fingerprint -> ngram_fingerprint)
    reruns matching with the new algorithm's default param."""
    _upload_and_map(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ngram_fingerprint", "n": "2"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    # Confirm session was actually updated by checking the full page reflects it.
    page = client.get("/algorithm")
    assert 'value="ngram_fingerprint"' in page.text


def test_recompute_change_radius_reruns_matching_with_new_threshold(client):
    """AC-M4-8: changing the Radius value reruns matching with the new value."""
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "levenshtein", "threshold": "0"},
        follow_redirects=False,
    )
    # threshold=0 -> "123 Main St" vs "123 MAIN ST." won't match (not identical).
    no_match_page = client.get("/algorithm")
    assert "results-empty-state" in no_match_page.text

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "levenshtein", "threshold": "10"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    # threshold=10 should now find the near-duplicate pair.
    assert "results-empty-state" not in response.text


def test_recompute_change_ngram_size_reruns_matching(client):
    """AC-M4-8: changing N-Gram size reruns matching with the new n value."""
    _upload_and_map(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ngram_fingerprint", "n": "3"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    page = client.get("/algorithm")
    assert 'value="3"' in page.text or 'value="ngram_fingerprint"' in page.text


# ---------------------------------------------------------------------------
# AC-M4-9 — invalid Radius/N-Gram size rejected without crashing the table
# ---------------------------------------------------------------------------


def test_recompute_invalid_levenshtein_threshold_negative_returns_422(client):
    _upload_and_map_with_duplicates(client)
    # Establish a known-good baseline first.
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "levenshtein", "threshold": "5"},
        follow_redirects=False,
    )

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "levenshtein", "threshold": "-1"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "flash-error" in response.text

    # session.algorithm_params not updated -- baseline (threshold=5) persists.
    page = client.get("/algorithm")
    assert 'value="5"' in page.text


def test_recompute_invalid_ncd_threshold_zero_returns_422(client):
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ncd", "threshold": "0"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "flash-error" in response.text


def test_recompute_invalid_ncd_threshold_above_ten_returns_422(client):
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ncd", "threshold": "11"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_recompute_invalid_ngram_size_zero_returns_422(client):
    _upload_and_map(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ngram_fingerprint", "n": "0"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "positive integer" in response.text.lower()


def test_recompute_invalid_ngram_size_non_integer_returns_422(client):
    _upload_and_map(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ngram_fingerprint", "n": "abc"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_recompute_invalid_param_does_not_mutate_session_or_run_matching(client):
    """AC-M4-9: invalid param submission does not update session.algorithm_params
    and does not invoke run_matching — the previously valid table is preserved."""
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )
    good_page = client.get("/algorithm")
    assert 'value="fingerprint"' in good_page.text

    bad = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "ngram_fingerprint", "n": "-5"},
        follow_redirects=False,
    )
    assert bad.status_code == 422

    page_after = client.get("/algorithm")
    # Still fingerprint -- the bad ngram_fingerprint submission never persisted.
    assert 'value="fingerprint"' in page_after.text
    assert "selected" in page_after.text


def test_recompute_unknown_algorithm_key_returns_422(client):
    _upload_and_map(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "not_a_real_algorithm"},
        follow_redirects=False,
    )

    assert response.status_code == 422


def test_recompute_without_mapping_redirects_to_mapping(client):
    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"


# ---------------------------------------------------------------------------
# AC-M4-10 — GET /results redirects to /algorithm
# ---------------------------------------------------------------------------


def test_get_results_redirects_to_algorithm(client):
    response = client.get("/results", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/algorithm"


def test_get_results_redirects_regardless_of_session_state(client):
    """AC-M4-10: the redirect happens for any session state, not just an
    empty/fresh session."""
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.get("/results", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/algorithm"


# ---------------------------------------------------------------------------
# AC-M4-17 — every row's Merge? checkbox is unchecked on render
# ---------------------------------------------------------------------------


def test_results_table_renders_merge_checkbox_unchecked_by_default(client):
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert "pair-row-checkbox" in text
    assert "checked" not in text


# ---------------------------------------------------------------------------
# AC-M4-18 — Distance column shown for NN pairs, omitted for fingerprint pairs
# ---------------------------------------------------------------------------


def test_results_table_distance_column_shown_for_nn_pairs(client):
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "levenshtein", "threshold": "5"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    text = response.text
    assert "<th>Distance</th>" in text
    assert "pair-row-distance" in text


def test_results_table_distance_column_omitted_for_fingerprint_pairs(client):
    _upload_and_map_with_duplicates(client)

    response = client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    text = response.text
    assert "<th>Distance</th>" not in text
    assert "pair-row-distance" not in text


# ---------------------------------------------------------------------------
# AC-M4-19 — each row renders both addresses as clickable elements
# ---------------------------------------------------------------------------


def test_results_table_renders_two_addresses_per_row_as_clickable_elements(client):
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    assert text.count('class="pair-row-address"') == 2
    assert 'data-row-index="0"' in text
    assert 'data-row-index="1"' in text
    assert 'data-address="123 Main St"' in text
    assert 'data-address="123 MAIN ST."' in text


# ---------------------------------------------------------------------------
# AC-M4-20 — New cell value input is not readonly or disabled
# ---------------------------------------------------------------------------


def test_new_cell_value_input_is_not_readonly_or_disabled(client):
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.get("/algorithm")

    assert response.status_code == 200
    text = response.text
    import re

    match = re.search(r'<input[^>]*class="field pair-row-new-value"[^>]*>', text)
    assert match
    assert "readonly" not in match.group(0)
    assert "disabled" not in match.group(0)


# ---------------------------------------------------------------------------
# AC-M4-24 — no per-pair accept/reject endpoints exist
# ---------------------------------------------------------------------------


def _all_api_routes():
    """Flatten every `APIRoute` registered on `app`, including those nested
    inside FastAPI's `_IncludedRouter` wrappers (used by `app.include_router`
    in this FastAPI version) so route-table assertions see the real leaf
    routes rather than the opaque wrapper objects."""
    routes = []
    for route in app.router.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append(route)
        elif type(route).__name__ == "_IncludedRouter":
            routes.extend(route.original_router.routes)
    return routes


def test_no_accept_reject_or_representative_endpoints_registered():
    """AC-M4-24: statically verify the FastAPI route table has no
    POST /results/pair/{id}/accept|reject|representative route."""
    paths = {route.path for route in _all_api_routes()}

    assert "/results/pair/{id}/accept" not in paths
    assert "/results/pair/{id}/reject" not in paths
    assert "/results/pair/{id}/representative" not in paths
    for path in paths:
        assert "/pair/" not in path


def test_only_merge_is_a_mutating_post_route_on_results_flow():
    """AC-M4-24: the only mutating route reachable from the results table is
    POST /merge."""
    post_paths = {route.path for route in _all_api_routes() if "POST" in (route.methods or set())}
    assert "/merge" in post_paths
    # No POST /results* route at all (GET /results is a redirect, not a POST handler).
    assert "/results" not in post_paths


# ---------------------------------------------------------------------------
# AC-M4-37 — no inline style= attributes (FR-9.3 regression check)
# ---------------------------------------------------------------------------


def test_algorithm_html_has_no_inline_style_attribute():
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    text = (repo_root / "app" / "templates" / "algorithm.html").read_text(encoding="utf-8")

    import re

    assert not re.search(r"""\sstyle\s*=\s*['"]""", text)


def test_results_table_partial_has_no_inline_style_attribute():
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    for filename in ("_results_table.html", "_pair_row.html"):
        text = (repo_root / "app" / "templates" / "partials" / filename).read_text(encoding="utf-8")
        import re

        assert not re.search(r"""\sstyle\s*=\s*['"]""", text), filename
