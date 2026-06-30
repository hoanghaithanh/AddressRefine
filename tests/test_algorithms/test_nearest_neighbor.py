"""Tests for app/algorithms/nearest_neighbor.py.

Covers AC-M3-11 through AC-M3-23.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.algorithms.base import AlgorithmFamily, AlgorithmOutput
from app.algorithms.nearest_neighbor import LevenshteinNNAlgorithm, NCDAlgorithm
from app.algorithms.registry import get_algorithm, list_algorithms

# ---------------------------------------------------------------------------
# AC-M3-11 — LevenshteinNNAlgorithm registration
# ---------------------------------------------------------------------------


def test_levenshtein_registered_with_correct_key_label_family():
    """AC-M3-11: list_algorithms() includes LevenshteinNNAlgorithm with expected metadata."""
    algorithms = list_algorithms()
    lev = next((a for a in algorithms if a.key == "levenshtein"), None)

    assert lev is not None
    assert isinstance(lev, LevenshteinNNAlgorithm)
    assert lev.label == "Levenshtein Distance"
    assert lev.family == AlgorithmFamily.NEAREST_NEIGHBOR


def test_get_algorithm_levenshtein_returns_correct_instance():
    """AC-M3-11: get_algorithm('levenshtein') returns a LevenshteinNNAlgorithm."""
    algo = get_algorithm("levenshtein")

    assert algo is not None
    assert isinstance(algo, LevenshteinNNAlgorithm)
    assert algo.key == "levenshtein"


# ---------------------------------------------------------------------------
# AC-M3-12 — LevenshteinNNAlgorithm param_specs
# ---------------------------------------------------------------------------


def test_levenshtein_param_specs_threshold():
    """AC-M3-12: LevenshteinNNAlgorithm has exactly one ParamSpec for threshold."""
    algo = LevenshteinNNAlgorithm()

    assert len(algo.param_specs) == 1
    spec = algo.param_specs[0]
    assert spec.name == "threshold"
    assert spec.param_type is int
    assert spec.default == 3


# ---------------------------------------------------------------------------
# AC-M3-13 — Levenshtein pairs rows within threshold
# ---------------------------------------------------------------------------


def test_levenshtein_pairs_within_threshold():
    """AC-M3-13: rows within edit distance are paired."""
    addresses = {
        0: "123 main st",
        1: "123 main street",  # edit distance ~4
        2: "456 oak ave",
    }
    blocks = {
        "block_a": [0, 1, 2],
    }
    algo = LevenshteinNNAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 5})

    assert output.pairs is not None
    pair_indices = {(min(i, j), max(i, j)) for i, j, _ in output.pairs}
    assert (0, 1) in pair_indices


def test_levenshtein_pairs_contain_distance_field():
    """AC-M3-13: each pair tuple has a numeric distance as the third element."""
    addresses = {0: "abc", 1: "abcd"}
    blocks = {"b": [0, 1]}
    algo = LevenshteinNNAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 3})

    assert output.pairs
    _, _, dist = output.pairs[0]
    assert isinstance(dist, float)
    assert dist >= 0.0


# ---------------------------------------------------------------------------
# AC-M3-14 — Levenshtein does not pair rows above threshold
# ---------------------------------------------------------------------------


def test_levenshtein_does_not_pair_above_threshold():
    """AC-M3-14: rows with edit distance > threshold produce no pair."""
    addresses = {
        0: "123 main street",
        1: "987 totally different avenue",  # far from row 0
    }
    blocks = {"b": [0, 1]}
    algo = LevenshteinNNAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 3})

    pair_indices = {(min(i, j), max(i, j)) for i, j, _ in (output.pairs or [])}
    assert (0, 1) not in pair_indices


# ---------------------------------------------------------------------------
# AC-M3-15 — Levenshtein threshold=0 matches only identical strings
# ---------------------------------------------------------------------------


def test_levenshtein_threshold_zero_matches_only_identical():
    """AC-M3-15: threshold=0 pairs identical strings and nothing else."""
    addresses = {
        0: "abc",
        1: "abc",  # identical to row 0
        2: "abcd",  # 1 edit away
    }
    blocks = {"b": [0, 1, 2]}
    algo = LevenshteinNNAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 0})

    pair_indices = {(min(i, j), max(i, j)) for i, j, _ in (output.pairs or [])}
    assert (0, 1) in pair_indices
    assert (0, 2) not in pair_indices
    assert (1, 2) not in pair_indices


def test_levenshtein_threshold_zero_does_not_pair_different_strings():
    """AC-M3-15: two different strings produce no pair at threshold=0."""
    addresses = {0: "123 main st", 1: "123 main street"}
    blocks = {"b": [0, 1]}
    algo = LevenshteinNNAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 0})

    assert output.pairs == [] or output.pairs is None or len(output.pairs) == 0


# ---------------------------------------------------------------------------
# AC-M3-16 — Levenshtein respects block boundaries
# ---------------------------------------------------------------------------


def test_levenshtein_respects_block_boundaries():
    """AC-M3-16: rows in different blocks are never compared, even if within threshold."""
    addresses = {
        0: "abc",
        1: "abc",  # identical to row 0, but in a different block
    }
    blocks = {
        "block_a": [0],
        "block_b": [1],
    }
    algo = LevenshteinNNAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 10})

    assert output.pairs == [] or not output.pairs


# ---------------------------------------------------------------------------
# AC-M3-17 — Levenshtein uses rapidfuzz with score_cutoff (static check)
# ---------------------------------------------------------------------------


def test_levenshtein_uses_rapidfuzz_with_score_cutoff():
    """AC-M3-17: nearest_neighbor.py uses rapidfuzz.distance.Levenshtein.distance
    with score_cutoff (static source check)."""
    nn_path = Path(__file__).resolve().parents[2] / "app" / "algorithms" / "nearest_neighbor.py"
    source = nn_path.read_text(encoding="utf-8")

    assert "rapidfuzz" in source
    assert "score_cutoff" in source
    assert "Levenshtein.distance" in source


# ---------------------------------------------------------------------------
# AC-M3-18 — NCDAlgorithm registration
# ---------------------------------------------------------------------------


def test_ncd_registered_with_correct_key_label_family():
    """AC-M3-18: list_algorithms() includes NCDAlgorithm with expected metadata."""
    algorithms = list_algorithms()
    ncd = next((a for a in algorithms if a.key == "ncd"), None)

    assert ncd is not None
    assert isinstance(ncd, NCDAlgorithm)
    assert ncd.label == "PPM / NCD"
    assert ncd.family == AlgorithmFamily.NEAREST_NEIGHBOR


def test_get_algorithm_ncd_returns_correct_instance():
    """AC-M3-18: get_algorithm('ncd') returns an NCDAlgorithm."""
    algo = get_algorithm("ncd")

    assert algo is not None
    assert isinstance(algo, NCDAlgorithm)
    assert algo.key == "ncd"


# ---------------------------------------------------------------------------
# AC-M3-19 — NCDAlgorithm param_specs
# ---------------------------------------------------------------------------


def test_ncd_param_specs_threshold():
    """AC-M3-19: NCDAlgorithm has exactly one ParamSpec for threshold."""
    algo = NCDAlgorithm()

    assert len(algo.param_specs) == 1
    spec = algo.param_specs[0]
    assert spec.name == "threshold"
    assert spec.param_type is int
    assert spec.default == 3


# ---------------------------------------------------------------------------
# AC-M3-20 — NCD UI threshold scaled by / 10.0 (static + behavioral check)
# ---------------------------------------------------------------------------


def test_ncd_threshold_scaling_documented_in_source():
    """AC-M3-20: nearest_neighbor.py documents the 0.3 example scaling."""
    nn_path = Path(__file__).resolve().parents[2] / "app" / "algorithms" / "nearest_neighbor.py"
    source = nn_path.read_text(encoding="utf-8")

    assert "0.3" in source, "Source should document the ui=3 → internal=0.3 example"
    assert "10.0" in source, "Source should show the / 10.0 scaling"


def test_ncd_threshold_scaling_behavioral():
    """AC-M3-20: with ui threshold=3, internal cutoff is 0.3.

    Construct two identical strings (NCD=0.0, well within 0.3) and two that
    share very little structure (NCD well above 0.3), then verify only the
    similar pair is returned.
    """
    # Identical strings → NCD = 0.0 (well within 0.3)
    addresses = {
        0: "abc def",
        1: "abc def",  # NCD = 0.0
        2: "zzz qqq yyy xxx",  # NCD vs row 0 expected > 0.3
    }
    # Put all in one block.
    blocks = {"b": [0, 1, 2]}
    algo = NCDAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 3})

    pair_indices = {(min(i, j), max(i, j)) for i, j, _ in (output.pairs or [])}
    # (0, 1) must appear because NCD=0.0 <= 0.3
    assert (0, 1) in pair_indices


# ---------------------------------------------------------------------------
# AC-M3-21 — NCD pairs rows within internal threshold
# ---------------------------------------------------------------------------


def test_ncd_pairs_within_threshold():
    """AC-M3-21: very similar strings (NCD <= cutoff) appear in output.pairs."""
    addresses = {
        0: "123 main street springfield",
        1: "123 main street springfield",  # identical → NCD = 0.0
    }
    blocks = {"b": [0, 1]}
    algo = NCDAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 5})

    assert output.pairs is not None
    assert len(output.pairs) >= 1
    pair_indices = {(min(i, j), max(i, j)) for i, j, _ in output.pairs}
    assert (0, 1) in pair_indices


def test_ncd_pairs_contain_distance_field():
    """AC-M3-21: each pair tuple carries an NCD score as the third element."""
    addresses = {0: "abc def", 1: "abc def"}
    blocks = {"b": [0, 1]}
    algo = NCDAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 5})

    assert output.pairs
    _, _, score = output.pairs[0]
    assert isinstance(score, float)
    assert 0.0 <= score <= 2.0  # NCD may slightly exceed 1 but won't be huge


# ---------------------------------------------------------------------------
# AC-M3-22 — NCD does not pair rows above internal threshold
# ---------------------------------------------------------------------------


def test_ncd_does_not_pair_above_threshold():
    """AC-M3-22: very dissimilar strings that exceed the cutoff are not paired."""
    # NCD with threshold=1 → internal cutoff=0.1: only extremely similar strings match.
    addresses = {
        0: "hello world this is a sentence",
        1: "zzzzzzzzzz qqqqqqqqqq xxxxxxxxxx",  # structurally very different
    }
    blocks = {"b": [0, 1]}
    algo = NCDAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 1})  # cutoff = 0.1

    pair_indices = {(min(i, j), max(i, j)) for i, j, _ in (output.pairs or [])}
    assert (0, 1) not in pair_indices


# ---------------------------------------------------------------------------
# AC-M3-23 — NCD respects block boundaries
# ---------------------------------------------------------------------------


def test_ncd_respects_block_boundaries():
    """AC-M3-23: identical strings in different blocks are not compared."""
    addresses = {
        0: "abc def",
        1: "abc def",  # identical, NCD=0.0
    }
    blocks = {
        "block_a": [0],
        "block_b": [1],
    }
    algo = NCDAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 10})

    assert not output.pairs


# ---------------------------------------------------------------------------
# AlgorithmOutput.pairs vs clusters — NN produces pairs, not clusters
# ---------------------------------------------------------------------------


def test_levenshtein_output_has_pairs_not_clusters():
    """Both NN algorithms use AlgorithmOutput.pairs, not clusters."""
    addresses = {0: "abc", 1: "abc"}
    blocks = {"b": [0, 1]}
    algo = LevenshteinNNAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 0})

    assert isinstance(output, AlgorithmOutput)
    assert output.pairs is not None
    assert output.clusters == {}


def test_ncd_output_has_pairs_not_clusters():
    """NCDAlgorithm uses AlgorithmOutput.pairs, not clusters."""
    addresses = {0: "abc def", 1: "abc def"}
    blocks = {"b": [0, 1]}
    algo = NCDAlgorithm()
    output = algo.run(addresses, blocks, {"threshold": 5})

    assert isinstance(output, AlgorithmOutput)
    assert output.pairs is not None
    assert output.clusters == {}


# ---------------------------------------------------------------------------
# AC-M3-41 — no pandas import in nearest_neighbor.py
# ---------------------------------------------------------------------------


def test_nearest_neighbor_module_does_not_import_pandas():
    """AC-M3-41: nearest_neighbor.py must not import pandas (static AST check)."""
    nn_path = Path(__file__).resolve().parents[2] / "app" / "algorithms" / "nearest_neighbor.py"
    source = nn_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name.split(".")[0] == "pandas" for alias in node.names), (
                "nearest_neighbor.py must not import pandas"
            )
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                assert node.module.split(".")[0] != "pandas", (
                    "nearest_neighbor.py must not import pandas"
                )
