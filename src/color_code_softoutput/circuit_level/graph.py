"""Labelled graph construction and exact binary incidence round trips."""
import hashlib
from collections.abc import Sequence
import numpy as np
from numpy.typing import ArrayLike
from scipy.sparse import csc_matrix, spmatrix
from .model import BoundaryRole, CircuitLevelGraph, DetectorMeta, RowRole, Stage2Mechanism


def build_graph(D: ArrayLike | spmatrix, logical_labels: ArrayLike, weights: ArrayLike, *,
                color: str = "synthetic", rows: Sequence[DetectorMeta] | None = None,
                probabilities: ArrayLike | None = None, source_ids: Sequence[tuple[int, ...]] | None = None,
                unsorted_ids: Sequence[int] | None = None, model_id: str | None = None,
                closed_temporal_boundary: bool = True) -> CircuitLevelGraph:
    """Freeze a graphlike matrix without merging columns.

    Args:
        D: Binary check matrix, shape (rows, mechanisms); up to two ones/column.
        logical_labels, weights: Shape (mechanisms,), bits and finite nonnegative
            natural-log costs. Original zero weights are supported.
        color, model_id: Provenance strings; hash is derived if absent.
        rows: All original row metadata, or synthetic physical row metadata.
        probabilities: Effective probabilities in (0,.5], or inferred from costs.
        source_ids, unsorted_ids: Per-column source tuples and pre-sort indices.
        closed_temporal_boundary: False is explicitly unsupported.
    Returns:
        Immutable completed multigraph with original row/column identities.
    Raises:
        ValueError: Invalid dimensions, parity, probabilities or graphlike support.
        NotImplementedError: Open temporal boundary requested.
    """
    if not closed_temporal_boundary:
        raise NotImplementedError("Open temporal boundaries/sliding windows are unsupported")
    matrix = csc_matrix(D, copy=True)
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    matrix.sort_indices()
    if not np.isin(matrix.data, [0, 1]).all():
        raise ValueError("D must be binary")
    n, m = matrix.shape
    labels, costs = np.asarray(logical_labels), np.asarray(weights, dtype=float)
    if labels.shape != (m,) or costs.shape != (m,) or not np.isin(labels, [0, 1]).all():
        raise ValueError("One binary label and weight required per column")
    if not np.isfinite(costs).all() or (costs < 0).any():
        raise ValueError("Finite nonnegative weights required")
    probs = 1 / (1 + np.exp(np.minimum(costs, 700))) if probabilities is None else np.asarray(probabilities)
    if probs.shape != (m,) or not np.isfinite(probs).all() or ((probs <= 0) | (probs > .5)).any():
        raise ValueError("Retained probabilities must be in (0, .5]")
    active = tuple(map(int, np.flatnonzero(matrix.getnnz(axis=1))))
    vertices = {row: v for v, row in enumerate(active)}
    if rows is None:
        rows = tuple(DetectorMeta(r, r, RowRole.PHYSICAL, r in vertices) for r in range(n))
    rows = tuple(rows)
    if len(rows) != n or any(r.row_id != i or r.active != (i in vertices) for i, r in enumerate(rows)):
        raise ValueError("Row metadata differs from matrix incidence")
    if any(r.active and r.role == RowRole.PADDING for r in rows):
        raise ValueError("Padding cannot have active incidence")
    source_ids = tuple((i,) for i in range(m)) if source_ids is None else tuple(source_ids)
    unsorted_ids = tuple(range(m)) if unsorted_ids is None else tuple(unsorted_ids)
    if len(source_ids) != m or sorted(unsorted_ids) != list(range(m)):
        raise ValueError("Invalid source or sort mapping")
    if model_id is None:
        payload = repr((matrix.shape, matrix.indptr.tolist(), matrix.indices.tolist(), labels.tolist(), costs.tolist()))
        model_id = hashlib.sha256(payload.encode()).hexdigest()
    edges = []
    for i in range(m):
        endpoints = tuple(map(int, matrix.indices[matrix.indptr[i]:matrix.indptr[i+1]]))
        if len(endpoints) > 2:
            raise ValueError("H2 is not graphlike")
        uv = tuple(vertices[r] for r in endpoints) + (len(active),) * (2-len(endpoints))
        role = (BoundaryRole.LOOP, BoundaryRole.MATCHING, BoundaryRole.INTERNAL)[len(endpoints)]
        stable = f"{model_id}:{color}:column:{unsorted_ids[i]}"
        edges.append(Stage2Mechanism(i, stable, uv, endpoints, int(labels[i]), float(probs[i]),
                                    float(costs[i]), tuple(map(int, source_ids[i])), int(unsorted_ids[i]), role))
    return CircuitLevelGraph(color, model_id, rows, active, tuple(edges), (n, m))


def incidence_matrix(graph: CircuitLevelGraph, *, original_rows: bool = False) -> csc_matrix:
    """Reconstruct D (active rows by default) from labelled graph endpoints.

    Args:
        graph: Frozen graph; loops have zero binary real incidence.
        original_rows: Restore the original H2 padding if True.
    Returns:
        uint8 sparse matrix, shape (active/original rows, mechanisms).
    """
    rr, cc = [], []
    for e in graph.mechanisms:
        for v in e.endpoints:
            if v != graph.b_star:
                rr.append(graph.active_rows[v] if original_rows else v)
                cc.append(e.column_id)
    n = graph.original_shape[0] if original_rows else graph.b_star
    return csc_matrix((np.ones(len(rr), dtype=np.uint8), (rr, cc)), shape=(n, len(graph.mechanisms)))
