"""Exact one-bit class test, internal balance gate, cut and logical cover."""
from collections import deque
import numpy as np
from numpy.typing import ArrayLike
from scipy.sparse import spmatrix
from .graph import incidence_matrix
from .model import AnalysisGraph, CircuitLevelGraph, CircuitLevelTopology, TopologyMethod


def _potential(graph, internal_only):
    n = graph.b_star if internal_only else graph.num_vertices
    adjacency = [[] for _ in range(n)]
    edges = [e for e in graph.mechanisms if not internal_only or len(e.endpoint_rows) == 2]
    for e in edges:
        u, v = e.endpoints
        adjacency[u].append((v, e.logical_label))
        adjacency[v].append((u, e.logical_label))
    g = [-1] * n
    for root in range(n):
        if g[root] != -1:
            continue
        g[root] = 0
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v, label in adjacency[u]:
                if g[v] == -1:
                    g[v] = g[u] ^ label
                    queue.append(v)
    conflicts = tuple(e.column_id for e in edges if g[e.endpoints[0]] ^ g[e.endpoints[1]] != e.logical_label)
    return tuple(g), conflicts


def gf2_rank(matrix: ArrayLike | spmatrix) -> int:
    """Return exact binary rank using packed Python integers (validation oracle).

    Args:
        matrix: Dense or sparse binary matrix, shape (rows, columns).
    Returns:
        Integer rank; no floating arithmetic is used.
    Raises:
        ValueError: Nonbinary or nonmatrix input.
    """
    a = matrix.toarray() if hasattr(matrix, "toarray") else np.asarray(matrix)
    if a.ndim != 2 or not np.isin(a, [0, 1]).all():
        raise ValueError("Binary matrix required")
    pivots = {}
    for row in a:
        bits = sum(1 << int(i) for i in np.flatnonzero(row))
        while bits:
            pivot = bits.bit_length()-1
            if pivot in pivots:
                bits ^= pivots[pivot]
            else:
                pivots[pivot] = bits
                break
    return len(pivots)


def rank_class_exists(graph: CircuitLevelGraph) -> bool:
    """Evaluate rank([D;L2])=rank(D)+1 independently of the graph-cycle test.

    Args: graph: Frozen one-observable graph.
    Returns: Whether its fixed-fiber opposite class exists.
    Notes: Dense expansion/elimination is an offline validation cost.
    """
    D = incidence_matrix(graph).toarray()
    L = np.array([e.logical_label for e in graph.mechanisms], dtype=np.uint8)
    return gf2_rank(np.vstack([D, L])) == gf2_rank(D) + 1


def build_cover(graph: CircuitLevelGraph) -> AnalysisGraph:
    """Build both lifts per original edge, preserving parallel arcs and labels.

    Args: graph: Completed base graph with one logical bit.
    Returns: Cached adjacency and all same-base-vertex opposite-sheet pairs.
    """
    adj = [[] for _ in range(2*graph.num_vertices)]
    for e in graph.mechanisms:
        u, v = e.endpoints
        for a in (0, 1):
            x, y = 2*u+a, 2*v+(a ^ e.logical_label)
            adj[x].append((y, e.column_id))
            adj[y].append((x, e.column_id))
    return AnalysisGraph(tuple(tuple(a) for a in adj), tuple((2*v, 2*v+1) for v in range(graph.num_vertices)))


def build_cut(graph: CircuitLevelGraph, potential: tuple[int, ...] | None = None) -> AnalysisGraph:
    """Build the two-boundary cut only after checking internal balance.

    Args:
        graph: Original completed graph.
        potential: Optional checked real-vertex binary gauge, shape (real vertices,).
    Returns: Cached adjacency with a single free-terminal pair.
    Raises: ValueError: Unbalanced internal graph or invalid supplied potential.
    """
    g, bad = _potential(graph, True)
    if bad:
        raise ValueError("Two-boundary cut requires internal balance")
    if potential is not None:
        g = tuple(potential)
        if len(g) != graph.b_star or any(x not in (0, 1) for x in g):
            raise ValueError("Invalid binary potential")
        if any(g[e.endpoints[0]] ^ g[e.endpoints[1]] != e.logical_label
               for e in graph.mechanisms if len(e.endpoint_rows) == 2):
            raise ValueError("Potential fails internal balance")
    b0, b1 = graph.b_star, graph.b_star+1
    adj = [[] for _ in range(graph.num_vertices+1)]
    for e in graph.mechanisms:
        u, v = e.endpoints
        if len(e.endpoint_rows) == 1:
            v = b0 + (e.logical_label ^ g[u])
        elif not e.endpoint_rows:
            u, v = b0, b0 + e.logical_label
        adj[u].append((v, e.column_id))
        adj[v].append((u, e.column_id))
    return AnalysisGraph(tuple(tuple(a) for a in adj), ((b0, b1),))


def preprocess_topology(graph: CircuitLevelGraph) -> CircuitLevelTopology:
    """Cache exact graph-structural gates in O(V+E), independent of shot syndrome.

    Args: graph: Immutable fully terminated retained graph.
    Returns: Class/balance flags, gauge, obstruction IDs and cached cut or cover.
    Raises: NotImplementedError: Open temporal boundary graph.
    Notes: Full-graph balance is equivalent to L2 in rowspan(D). The separate
        rank oracle checks this equivalence without incurring elimination per shot.
    """
    if not graph.closed_temporal_boundary:
        raise NotImplementedError("Closed temporal boundary required")
    g, bad = _potential(graph, True)
    _, full_bad = _potential(graph, False)
    if not full_bad:
        # No logical class: do not manufacture analysis boundaries for it.
        return CircuitLevelTopology(graph, False, not bad, g, bad, None, None)
    method = TopologyMethod.LOGICAL_COVER if bad else TopologyMethod.TWO_BOUNDARY
    analysis = build_cover(graph) if bad else build_cut(graph, g)
    return CircuitLevelTopology(graph, bool(full_bad), not bad, g, bad, method, analysis)
