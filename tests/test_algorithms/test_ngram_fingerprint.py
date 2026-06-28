"""Tests for app/algorithms/fingerprint.py::NGramFingerprintAlgorithm."""

from __future__ import annotations

from app.algorithms.fingerprint import NGramFingerprintAlgorithm


def test_default_n_is_2():
    """AC-M2-11: param_specs declares a default of 2 for n, and running with
    an empty params dict behaves identically to passing {"n": 2}."""
    algorithm = NGramFingerprintAlgorithm()

    n_spec = next(spec for spec in algorithm.param_specs if spec.name == "n")
    assert n_spec.default == 2

    addresses = {0: "abcab", 1: "bcaba"}
    output_default = algorithm.run(addresses, None, {})
    output_explicit = algorithm.run(addresses, None, {"n": 2})

    assert output_default.clusters == output_explicit.clusters


def test_ngram_key_construction_uses_hyphen_delimiter():
    """AC-M2-12: normalized "abcab" with n=2 produces key "ab-bc-ca"."""
    algorithm = NGramFingerprintAlgorithm()

    key = algorithm._ngram_key("abcab", 2)

    assert key == "ab-bc-ca"


def test_ngram_key_construction_via_public_run_clusters_matching_rows():
    algorithm = NGramFingerprintAlgorithm()
    # Both normalize (lowercase, strip punctuation, remove spaces) to "abcab".
    addresses = {0: "ab-cab", 1: "ABCAB"}

    output = algorithm.run(addresses, None, {"n": 2})

    assert len(output.clusters) == 1
    (key, rows) = next(iter(output.clusters.items()))
    assert key == "ab-bc-ca"
    assert sorted(rows) == [0, 1]


def test_strings_shorter_than_n_excluded():
    """AC-M2-13: a normalized string shorter than n characters is excluded
    from clustering, mirroring the blank-address exclusion of Fingerprint."""
    algorithm = NGramFingerprintAlgorithm()

    assert algorithm._ngram_key("a", 2) is None

    addresses = {0: "a", 1: "ab", 2: "ab"}
    output = algorithm.run(addresses, None, {"n": 2})

    all_clustered_rows = {row for rows in output.clusters.values() for row in rows}
    assert 0 not in all_clustered_rows
    assert all_clustered_rows == {1, 2}


def test_different_n_can_change_cluster_assignments():
    """AC-M2-14: n=2 vs n=3 are not required to produce identical clusters
    (property test confirming n is actually wired through). "aabaa" and
    "abaaa" share the same set of n=2 bigrams ({aa, ab, ba}, just in a
    different multiset) so they cluster together at n=2, but their n=3
    trigram sets differ entirely, so neither shares a key with anything
    at n=3 (verified directly: n=2 yields one 2-row cluster, n=3 yields
    none)."""
    algorithm = NGramFingerprintAlgorithm()
    addresses = {0: "aabaa", 1: "abaaa"}

    output_n2 = algorithm.run(addresses, None, {"n": 2})
    output_n3 = algorithm.run(addresses, None, {"n": 3})

    assert output_n2.clusters != output_n3.clusters
    assert len(output_n2.clusters) == 1
    assert output_n3.clusters == {}


def test_run_with_default_param_specs_default_used_when_n_missing_from_params():
    algorithm = NGramFingerprintAlgorithm()

    output = algorithm.run({0: "abcab"}, None, {})

    # n defaults to 2, and a singleton key produces no cluster.
    assert output.clusters == {}


def test_ngram_fingerprint_algorithm_metadata():
    algorithm = NGramFingerprintAlgorithm()

    assert algorithm.key == "ngram_fingerprint"
    assert len(algorithm.param_specs) == 1
    assert algorithm.param_specs[0].name == "n"
