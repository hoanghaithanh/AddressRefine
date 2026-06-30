"""Tests for app/algorithms/registry.py."""

from __future__ import annotations

from app.algorithms.fingerprint import FingerprintAlgorithm, NGramFingerprintAlgorithm
from app.algorithms.registry import get_algorithm, list_algorithms


def test_list_algorithms_includes_fingerprint_and_ngram():
    """AC-M2-3: list_algorithms() returns both M2 algorithms."""
    algorithms = list_algorithms()
    keys = [algo.key for algo in algorithms]

    assert "fingerprint" in keys
    assert "ngram_fingerprint" in keys
    assert any(isinstance(algo, FingerprintAlgorithm) for algo in algorithms)
    assert any(isinstance(algo, NGramFingerprintAlgorithm) for algo in algorithms)


def test_get_algorithm_fingerprint_returns_correct_instance():
    algorithm = get_algorithm("fingerprint")

    assert isinstance(algorithm, FingerprintAlgorithm)
    assert algorithm.key == "fingerprint"


def test_get_algorithm_ngram_fingerprint_returns_correct_instance():
    algorithm = get_algorithm("ngram_fingerprint")

    assert isinstance(algorithm, NGramFingerprintAlgorithm)
    assert algorithm.key == "ngram_fingerprint"


def test_get_algorithm_unknown_key_returns_none():
    assert get_algorithm("not_a_real_algorithm") is None


def test_list_algorithms_returns_a_new_list_each_call():
    """Callers should be able to mutate the returned list without affecting
    the registry's internal state."""
    first = list_algorithms()
    first.clear()

    second = list_algorithms()

    assert len(second) == 4  # fingerprint, ngram_fingerprint, levenshtein, ncd
