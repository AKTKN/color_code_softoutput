"""Original-graph metric-ball coverage, before any cut or cover transform."""
from heapq import heappop, heappush
import numpy as np
from numpy.typing import ArrayLike
from .model import CircuitLevelGraph

GROWTH_CONVENTION = "sparse_blossom_final_defect_metric_balls_v1"
COVERAGE_CONVENTION = "original_completed_labelled_stage2_graph_v1"


def residual_weights(graph: CircuitLevelGraph, radii: ArrayLike | None) -> np.ndarray:
    """Propagate exported balls on the original completed graph and retain labels.

    Args:
        graph: Original graph, never a cut or cover; finite nonnegative weights.
        radii: Shape (graph.num_vertices,), finite nonnegative radii in matching
            weight units. None is unavailable growth and is refused.
    Returns:
        Uncovered edge lengths in original column order, shape (mechanisms,).
        A loop subtracts twice its endpoint coverage; zero-cost odd loops survive.
    Raises:
        ValueError: Missing growth, invalid shape, negative or nonfinite radius.
    """
    if radii is None:
        raise ValueError("Growth unavailable: explicit radii are required")
    h = np.array(radii, dtype=float, copy=True)
    if h.shape != (graph.num_vertices,) or not np.isfinite(h).all() or (h < 0).any():
        raise ValueError("One finite nonnegative radius per original vertex required")
    adjacency = [[] for _ in range(graph.num_vertices)]
    for e in graph.mechanisms:
        u, v = e.endpoints
        adjacency[u].append((v, e.weight))
        adjacency[v].append((u, e.weight))
    heap = []
    for u, r in enumerate(h):
        if r > 0:
            heappush(heap, (-r, u))
    while heap:
        negative, u = heappop(heap)
        r = -negative
        if r != h[u]:
            continue
        for v, w in adjacency[u]:
            candidate = r-w
            if candidate > h[v]:
                h[v] = candidate
                heappush(heap, (-candidate, v))
    return np.array([max(0., e.weight-h[e.endpoints[0]]-h[e.endpoints[1]]) for e in graph.mechanisms])
