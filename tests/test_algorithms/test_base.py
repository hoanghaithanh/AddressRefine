"""Tests for app/algorithms/base.py."""

from __future__ import annotations

from app.algorithms.base import AlgorithmFamily, AlgorithmOutput, MatchingAlgorithm, ParamSpec


def test_matching_algorithm_abc_shape():
    """AC-M2-1: MatchingAlgorithm declares key/label/family/param_specs and an
    abstract run() method with the documented signature.

    `key`/`label`/`family` are bare class-variable annotations (no class-level
    default), so they're declared in __annotations__ rather than retrievable
    via hasattr() on the class itself -- each concrete subclass assigns them.
    """
    assert "key" in MatchingAlgorithm.__annotations__
    assert "label" in MatchingAlgorithm.__annotations__
    assert "family" in MatchingAlgorithm.__annotations__
    # Default param_specs is an empty list for algorithms with no parameters.
    assert MatchingAlgorithm.param_specs == []

    assert "run" in MatchingAlgorithm.__abstractmethods__


def test_matching_algorithm_cannot_be_instantiated_directly():
    """It's an ABC: instantiating it without implementing run() should fail."""
    import pytest

    with pytest.raises(TypeError):
        MatchingAlgorithm()


def test_param_spec_holds_name_label_type_default():
    spec = ParamSpec(name="n", label="N-gram size", param_type=int, default=2)

    assert spec.name == "n"
    assert spec.label == "N-gram size"
    assert spec.param_type is int
    assert spec.default == 2


def test_algorithm_output_carries_clusters_for_key_collision():
    """AC-M2-2: AlgorithmOutput.clusters is populated for key-collision algorithms,
    and .pairs is None/empty for this family."""
    output = AlgorithmOutput(clusters={"123 main st": [0, 2]}, pairs=None)

    assert output.clusters == {"123 main st": [0, 2]}
    assert not output.pairs


def test_algorithm_output_defaults_to_empty_clusters_and_none_pairs():
    output = AlgorithmOutput()

    assert output.clusters == {}
    assert output.pairs is None


def test_algorithm_family_has_key_collision_and_nearest_neighbor():
    assert AlgorithmFamily.KEY_COLLISION == "key_collision"
    assert AlgorithmFamily.NEAREST_NEIGHBOR == "nearest_neighbor"
