"""Tests for app/algorithms/fingerprint.py::FingerprintAlgorithm."""

from __future__ import annotations

from app.algorithms.fingerprint import FingerprintAlgorithm


def test_normalization_case_and_punctuation_insensitive():
    """AC-M2-4: "123 Main St." and "123 MAIN ST" produce the same key."""
    algorithm = FingerprintAlgorithm()
    addresses = {0: "123 Main St.", 1: "123 MAIN ST"}

    output = algorithm.run(addresses, None, {})

    assert len(output.clusters) == 1
    (cluster_rows,) = output.clusters.values()
    assert sorted(cluster_rows) == [0, 1]


def test_normalization_collapses_whitespace():
    """AC-M2-5: multiple consecutive spaces collapse to a single space."""
    algorithm = FingerprintAlgorithm()
    addresses = {0: "123  Main   St", 1: "123 Main St"}

    output = algorithm.run(addresses, None, {})

    assert len(output.clusters) == 1
    (cluster_rows,) = output.clusters.values()
    assert sorted(cluster_rows) == [0, 1]


def test_token_order_does_not_affect_key():
    """AC-M2-6: same tokens in a different order produce the same key."""
    algorithm = FingerprintAlgorithm()
    addresses = {0: "3 King St Unit 123", 1: "Unit 123 3 King St"}

    output = algorithm.run(addresses, None, {})

    assert len(output.clusters) == 1
    (cluster_rows,) = output.clusters.values()
    assert sorted(cluster_rows) == [0, 1]


def test_duplicate_tokens_deduplicated():
    """AC-M2-7: a repeated word appears only once in the resulting key."""
    algorithm = FingerprintAlgorithm()

    key = algorithm._fingerprint_key("the the corner store")

    assert key == "corner store the"
    assert key.split(" ").count("the") == 1


def test_non_matching_addresses_not_clustered():
    """AC-M2-8: different addresses get different keys and no cluster."""
    algorithm = FingerprintAlgorithm()
    addresses = {0: "123 Main St", 1: "456 Oak Ave"}

    output = algorithm.run(addresses, None, {})

    assert output.clusters == {}


def test_blank_address_excluded_from_clustering():
    """AC-M2-9: a blank/whitespace-only address never appears in a cluster."""
    algorithm = FingerprintAlgorithm()
    addresses = {0: "123 Main St", 1: "123 Main St", 2: "", 3: "   "}

    output = algorithm.run(addresses, None, {})

    all_clustered_rows = {row for rows in output.clusters.values() for row in rows}
    assert 2 not in all_clustered_rows
    assert 3 not in all_clustered_rows
    assert all_clustered_rows == {0, 1}


def test_singleton_key_produces_no_cluster():
    """AC-M2-10 (algorithm-level half): a row whose key matches no other row
    does not appear in any cluster in the raw AlgorithmOutput."""
    algorithm = FingerprintAlgorithm()
    addresses = {0: "123 Main St", 1: "456 Oak Ave"}

    output = algorithm.run(addresses, None, {})

    assert output.clusters == {}


def test_fingerprint_algorithm_metadata():
    algorithm = FingerprintAlgorithm()

    assert algorithm.key == "fingerprint"
    assert algorithm.param_specs == []


def test_run_with_empty_addresses_returns_empty_clusters():
    algorithm = FingerprintAlgorithm()

    output = algorithm.run({}, None, {})

    assert output.clusters == {}
    assert output.pairs is None
