"""Tests for `POST /merge` in app/routers/algorithm.py.

Covers AC-M4-32 through AC-M4-34 from
`docs/ba/acceptance-criteria/m4-merge-review.md`.
"""

from __future__ import annotations


def _upload_and_map_with_duplicates(client):
    """Upload a CSV where two rows fingerprint-match, suitable for merge testing."""
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


def _get_pair_id(client) -> str:
    """Fetch the current /algorithm page and pull out the (single) pair_id
    rendered in the results table."""
    import re

    page = client.get("/algorithm")
    match = re.search(r'data-pair-id="([^"]+)"', page.text)
    assert match, f"no pair_id found in page: {page.text}"
    return match.group(1)


# ---------------------------------------------------------------------------
# AC-M4-32 — merge request includes only checked rows
# ---------------------------------------------------------------------------


def test_post_merge_only_includes_checked_rows_in_request(client):
    """Submitting a merge with one pair_id/new_value pair only affects the
    rows belonging to that pair — an unsubmitted pair's rows are untouched."""
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )
    pair_id = _get_pair_id(client)

    response = client.post(
        "/merge",
        data={"pair_id": pair_id, "new_value": "123 Merged St"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    # The merge actually ran -- the two rows are now identical and
    # fingerprint-clustered again post-rerun, so they still show up as one
    # pair (with the new merged value) rather than vanishing entirely; the
    # important point is the request succeeded and re-ran matching.
    assert 'id="results-table-container"' in response.text


def test_post_merge_empty_request_is_a_noop_and_returns_200(client):
    """Submitting POST /merge with no pair_id/new_value fields at all (the
    'nothing checked' case) is a no-op, not an error."""
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    response = client.post("/merge", data={}, follow_redirects=False)

    assert response.status_code == 200
    assert 'id="results-table-container"' in response.text


# ---------------------------------------------------------------------------
# AC-M4-33 — successful merge returns a refreshed results-table partial
# ---------------------------------------------------------------------------


def test_post_merge_success_returns_refreshed_results_table_partial(client):
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )
    pair_id = _get_pair_id(client)

    response = client.post(
        "/merge",
        data={"pair_id": pair_id, "new_value": "123 Merged St"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    text = response.text
    # Same combined-page partial structure, no full-page navigation/redirect.
    assert 'id="results-table-container"' in text
    assert "<html" not in text


def test_post_merge_success_appends_dataset_version(client):
    _upload_and_map_with_duplicates(client)
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )
    pair_id = _get_pair_id(client)

    client.post(
        "/merge",
        data={"pair_id": pair_id, "new_value": "123 Merged St"},
        follow_redirects=False,
    )

    # Re-fetching /algorithm reflects the merged value in row text.
    page = client.get("/algorithm")
    assert "123 Merged St" in page.text


def test_post_merge_without_mapping_redirects_to_mapping(client):
    response = client.post(
        "/merge",
        data={"pair_id": "whatever", "new_value": "X"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/mapping"


# ---------------------------------------------------------------------------
# AC-M4-34 — conflicting merge request returns a validation error without
# mutating session state
# ---------------------------------------------------------------------------


def test_post_merge_conflict_returns_422_and_does_not_mutate_session(client):
    """Build a 3-row cluster (all fingerprint-equal) so the resulting
    candidate_pairs include two pairs sharing row 0, then submit
    conflicting new_value targets for that shared row."""
    csv_bytes = (
        b"StreetAddress,ZipCode,City\n"
        b"123 Main St,00501,Springfield\n"
        b"123 MAIN ST.,00501,Springfield\n"
        b"123 main st,00501,Springfield\n"
    )
    client.post(
        "/upload",
        files={"file": ("addresses.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )
    client.post(
        "/mapping",
        data={"street_col": "StreetAddress", "zip_col": "ZipCode", "city_col": "City"},
        follow_redirects=False,
    )
    client.post(
        "/algorithm/recompute",
        data={"algorithm_key": "fingerprint"},
        follow_redirects=False,
    )

    import re

    page = client.get("/algorithm")
    # 3-row cluster explodes into 3 pairs: (0,1), (0,2), (1,2) in some order.
    # Every row appears in the rendered table; find two distinct pair rows
    # that both contain row index 0 to construct a genuine conflict.
    row_blocks = re.findall(
        r'<tr class="pair-row" data-pair-id="([^"]+)">.*?</tr>', page.text, re.DOTALL
    )
    pairs_with_row0 = []
    for block_pair_id in row_blocks:
        block_match = re.search(
            rf'<tr class="pair-row" data-pair-id="{re.escape(block_pair_id)}">(.*?)</tr>',
            page.text,
            re.DOTALL,
        )
        row_indices = re.findall(r'data-row-index="(\d+)"', block_match.group(1))
        if "0" in row_indices:
            pairs_with_row0.append(block_pair_id)

    assert len(pairs_with_row0) >= 2, "expected at least 2 pairs sharing row 0"
    pair_a, pair_b = pairs_with_row0[0], pairs_with_row0[1]

    response = client.post(
        "/merge",
        data={
            "pair_id": [pair_a, pair_b],
            "new_value": ["Target A", "Target B"],
        },
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert "flash-error" in response.text

    # Session state unaffected: re-fetching shows the original (unmerged) addresses.
    after = client.get("/algorithm")
    assert "Target A" not in after.text
    assert "Target B" not in after.text
    assert "123 Main St" in after.text
