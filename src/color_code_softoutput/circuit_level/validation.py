"""Independent matrix/chain and hard-output invariants for retained models."""
import math
import numpy as np
from numpy.typing import ArrayLike
from typing import Any
from .graph import incidence_matrix
from .model import CircuitLevelGraph, Witness

WEIGHT_ATOL = 1e-9
WEIGHT_RTOL = 1e-10


def validate_witness(graph: CircuitLevelGraph, witness: Witness, residuals: ArrayLike, phi: float) -> None:
    """Check original matrix parity, source identity and residual cost independently.

    Args:
        graph: Original retained model; its source column order defines z.
        witness: Distinct original column support, including for zero phi.
        residuals: Shape (mechanisms,), costs in ordinary natural-log units.
        phi: Returned shortest-path value, finite and nonnegative.
    Returns: None on success.
    Raises: ValueError: Invalid IDs, nonzero syndrome, even logical parity or cost
        mismatch (absolute 1e-9, relative 1e-10).
    """
    ids = witness.column_ids
    if not ids or len(set(ids)) != len(ids) or any(i < 0 or i >= len(graph.mechanisms) for i in ids):
        raise ValueError("Witness must have nonempty distinct original column IDs")
    if witness.stable_ids != tuple(graph.mechanisms[i].stable_id for i in ids):
        raise ValueError("Witness provenance mismatch")
    z = np.zeros(len(graph.mechanisms), dtype=np.uint8)
    z[list(ids)] = 1
    if np.any((incidence_matrix(graph) @ z) % 2):
        raise ValueError("Witness has nonzero D z")
    if sum(graph.mechanisms[i].logical_label for i in ids) % 2 != 1:
        raise ValueError("Witness has even L2 z")
    cost = math.fsum(float(residuals[i]) for i in ids)
    if not math.isfinite(phi) or any(not math.isclose(cost, x, abs_tol=WEIGHT_ATOL, rel_tol=WEIGHT_RTOL)
                                   for x in (phi, witness.cost)):
        raise ValueError("Witness cost differs from phi")


def validate_correction(graph: CircuitLevelGraph, corrections: ArrayLike, syndromes: ArrayLike) -> None:
    """Require D f=s, including inactive original rows.

    Args: graph: Original model; corrections/syndromes: binary arrays of shape
        (shots, mechanisms)/(shots, original H2 rows).
    Returns: None on success.
    Raises: ValueError: Shapes, binary values, or any supplied constraint fails.
    """
    f, s = np.asarray(corrections), np.asarray(syndromes)
    if f.ndim != 2 or s.shape != (len(f), graph.original_shape[0]) or f.shape[1] != graph.original_shape[1]:
        raise ValueError("Correction/syndrome shape mismatch")
    if not np.isin(f, [0, 1]).all() or not np.isin(s, [0, 1]).all():
        raise ValueError("Binary correction/syndrome required")
    actual = f.astype(np.uint8) @ incidence_matrix(graph, original_rows=True).T % 2
    if not np.array_equal(actual, s):
        raise ValueError("Stage-2 correction violates D f = s")


def validate_hard_invariance(prediction: ArrayLike, extra: dict[str, Any], reference_prediction: ArrayLike,
                            reference_extra: dict[str, Any]) -> None:
    """Require bitwise identical predictions, ordinary weights, colors and corrections.

    Args: prediction/reference_prediction: (shots,) bits; extra/reference_extra:
        ordinary full-output dictionaries. Failure labels then agree for any
        shared actual observable. Float weights are compared exactly.
    Returns: None on success.
    Raises: ValueError: Any hard product differs.
    """
    if not np.array_equal(prediction, reference_prediction):
        raise ValueError("Hard prediction changed")
    for key in ("weights", "best_colors", "error_preds"):
        if not np.array_equal(extra[key], reference_extra[key]):
            raise ValueError(f"Hard {key} changed")
