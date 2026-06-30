"""Normalized Compression Distance (NCD) helper.

NCD is a parameter-free, compression-based similarity measure. Two strings
are "close" if compressing them together doesn't cost much more than
compressing each individually — i.e. they share structure / information.

This module never imports `pandas` or any compute-backend type. It only
depends on the Python standard library (``bz2``).

Formula used (symmetrized):
    NCD(a, b) = (C(a+b) - min(C(a), C(b))) / max(C(a), C(b))

where ``C(x)`` is the compressed length of ``x``. To guarantee symmetry we
average the result for both concatenation orders:
    NCD(a, b) = ((C(ab) - min(Ca, Cb)) / max(Ca, Cb)
                 + (C(ba) - min(Ca, Cb)) / max(Ca, Cb)) / 2

Edge cases:
- Both strings empty → 0.0 (identical, distance zero).
- One string empty and one non-empty → compression of the empty side may
  produce a tiny compressed length, so the formula handles it naturally.
"""

from __future__ import annotations

import bz2


def normalized_compression_distance(a: str, b: str) -> float:
    """Return the Normalized Compression Distance between strings ``a`` and ``b``.

    Uses ``bz2`` for compression. Returns a value in [0.0, 1.0] (in theory;
    practical NCD values may slightly exceed 1.0 due to compressor overhead,
    but this is rare for short strings).

    Special cases:
    - ``a == b == ""`` (both empty) → ``0.0``
    - ``a == b`` (identical non-empty) → approximately ``0.0``

    Args:
        a: First string.
        b: Second string.

    Returns:
        NCD score. Lower means more similar; 0.0 means identical.
    """
    # Short-circuit identical strings (including both empty) — bz2 header
    # overhead means C(aa) > C(a) even for identical strings, so we must
    # explicitly return 0.0 rather than letting the formula produce a small
    # positive artifact.
    if a == b:
        return 0.0

    bytes_a = a.encode("utf-8")
    bytes_b = b.encode("utf-8")

    ca = len(bz2.compress(bytes_a))
    cb = len(bz2.compress(bytes_b))

    # Guard against both compressed lengths being 0 (shouldn't happen for
    # non-empty inputs with bz2, but be safe).
    max_c = max(ca, cb)
    if max_c == 0:
        return 0.0

    min_c = min(ca, cb)

    cab = len(bz2.compress(bytes_a + bytes_b))
    cba = len(bz2.compress(bytes_b + bytes_a))

    # Average over both concatenation orders for symmetry.
    ncd = ((cab - min_c) / max_c + (cba - min_c) / max_c) / 2.0
    return ncd
