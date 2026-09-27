"""Exact shortest logical residual support with original mechanism witnesses."""
from heapq import heappop, heappush
import math
import numpy as np
from numpy.typing import ArrayLike
from .logical_topology import build_cover
from .model import CircuitLevelTopology, CircuitLevelSwimResult, SwimStatus, TopologyMethod, Witness
from .validation import validate_witness


def _shortest(adjacency, weights, source, target, ceiling=math.inf):
    distances = [math.inf] * len(adjacency)
    distances[source] = 0.
    previous = {}
    queue = [(0., source)]
    while queue:
        cost, u = heappop(queue)
        if cost != distances[u]:
            continue
        if cost >= ceiling:
            break
        if u == target:
            route = []
            while u != source:
                u, edge = previous[u]
                route.append(edge)
            return cost, route
        for v, edge in adjacency[u]:
            candidate = cost + weights[edge]
            # Strict relaxation keeps predecessor chains acyclic even at zero cost.
            if candidate < distances[v]:
                distances[v] = candidate
                previous[v] = (u, edge)
                heappush(queue, (candidate, v))
    return math.inf, None


def compute_circuit_level_swim(topology: CircuitLevelTopology, residuals: ArrayLike, *,
                               return_witness: bool = True, force_cover: bool = False) -> CircuitLevelSwimResult:
    """Compute min{wbar(z): Dz=0, L2 z=1} with no additional matching growth.

    Args:
        topology: Preprocessed closed-memory labelled model.
        residuals: Finite nonnegative costs, shape (mechanisms,), in ordinary
            matching units, computed on the original graph.
        return_witness: Include verified original-column support if True.
        force_cover: Use the exact general cover for cut-equivalence validation.
    Returns:
        Per-color geometric result; absent class returns +inf/None explicitly.
        certification_flag remains False for arbitrary/production residuals.
    Raises:
        ValueError: Invalid residuals or witness parity/cost inconsistency.
        RuntimeError: Structural class exists but shortest search finds none.
    """
    graph = topology.graph
    weights = np.asarray(residuals, dtype=float)
    if weights.shape != (len(graph.mechanisms),) or not np.isfinite(weights).all() or (weights < 0).any():
        raise ValueError("Finite nonnegative residual per original column required")
    method = TopologyMethod.LOGICAL_COVER if force_cover else topology.method
    if not topology.class_exists:
        return CircuitLevelSwimResult(math.inf, None, None, False, topology.balance_passed,
                                     SwimStatus.NO_OPPOSITE_CLASS)
    analysis = build_cover(graph) if force_cover else topology.analysis
    if analysis is None:
        raise ValueError("Missing preprocessed logical topology")
    best, route = math.inf, None
    for source, target in analysis.pairs:
        cost, candidate = _shortest(analysis.adjacency, weights, source, target, best)
        if cost < best:
            best, route = cost, candidate
        if best == 0:
            break
    if route is None:
        raise RuntimeError("Opposite class exists but analysis search found no witness")
    support = set()
    for edge in route:
        support.symmetric_difference_update((edge,))
    ids = tuple(sorted(support))
    witness = Witness(ids, tuple(graph.mechanisms[i].stable_id for i in ids),
                      math.fsum(float(weights[i]) for i in ids))
    # Check even when the caller omits the witness from its returned table.
    validate_witness(graph, witness, weights, best)
    return CircuitLevelSwimResult(float(best), witness if return_witness else None, method,
                                 True, topology.balance_passed, SwimStatus.OK)
