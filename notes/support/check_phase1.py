"""Finite Phase-1 proof checks, not decoder calibration or a production decoder.

Run from the repository root: python notes/support/check_phase1.py
Requires numpy and scipy. Exhausts d=3 chains/fibers in all colors; checks
larger-family incidence/ranks, optimal dual certificates, interval contraction,
and physical logical witnesses. Fixed inputs, no statistical benchmarking.
LP calculations use floating-point HiGHS with checks at tolerance 1e-8;
they are numerical sanity checks, not exact rational certificates.
"""
from itertools import combinations
import heapq
import numpy as np
from scipy.optimize import linprog

COLORS = ("r", "g", "b")
NEIGHBORS = ((-1, 1), (0, 1), (1, 0), (1, -1), (0, -1), (-1, 0))


def rank2(a):
    a = np.array(a, dtype=np.uint8, copy=True)
    row = 0
    for col in range(a.shape[1]):
        pivots = np.flatnonzero(a[row:, col])
        if len(pivots):
            p = row + pivots[0]
            a[[row, p]] = a[[p, row]]
            for r in range(row + 1, len(a)):
                if a[r, col]:
                    a[r] ^= a[row]
            row += 1
    return row


def patch(d, c):
    t = (d - 1) // 2
    limit = 3 * t
    sites = [(i, j) for i in range(limit + 1) for j in range(limit + 1 - i)]
    faces = [v for v in sites if (v[0] - v[1]) % 3 == 2]
    qubits = [v for v in sites if v not in faces]
    qi = {q: i for i, q in enumerate(qubits)}
    fc = {f: ("g", "b", "r")[f[1] % 3] for f in faces}
    supports = {}
    primal = {}
    for f in faces:
        support = [(f[0] + di, f[1] + dj) for di, dj in NEIGHBORS
                   if (f[0] + di, f[1] + dj) in qi]
        supports[f] = support
        for u, v in zip(support, support[1:] + support[:1]):
            primal.setdefault(tuple(sorted((u, v))), []).append(f)
    sides = {
        "r": {q for q in qubits if q[1] == 0},
        "g": {q for q in qubits if q[0] == 0},
        "b": {q for q in qubits if sum(q) == limit},
    }
    ec = {}
    for e, incident in primal.items():
        adjacent = {fc[f] for f in incident}
        if len(incident) == 1:
            side = next(a for a in COLORS if set(e) <= sides[a])
            adjacent.add(side)
        assert len(adjacent) == 2
        ec[e] = next(a for a in COLORS if a not in adjacent)
    real = [("f", f) for f in faces if fc[f] == c]
    real += [("e", e) for e in primal if ec[e] == c]
    vertices = real + [("b", 0), ("b", 1)]
    vi = {v: i for i, v in enumerate(vertices)}
    edges = []
    for q in qubits:
        fs = [f for f in faces if fc[f] == c and q in supports[f]]
        es = [e for e in primal if ec[e] == c and q in e]
        assert len(fs) <= 1 and len(es) <= 1 and fs + es
        u = ("f", fs[0]) if fs else ("b", 0)
        v = ("e", es[0]) if es else ("b", 1)
        edges.append((vi[u], vi[v]))
    incidence = np.zeros((len(vertices), len(qubits)), dtype=np.uint8)
    for i, (u, v) in enumerate(edges):
        incidence[u, i] ^= 1
        incidence[v, i] ^= 1
    h = np.array([[int(q in supports[f]) for q in qubits] for f in faces], dtype=np.uint8)
    dc = incidence[:-2]
    lam = np.zeros((len(faces), len(real)), dtype=np.uint8)
    for fi, f in enumerate(faces):
        if fc[f] == c:
            lam[fi, vi[("f", f)]] = 1
        else:
            for e in primal:
                if ec[e] == c and set(e) <= set(supports[f]):
                    lam[fi, vi[("e", e)]] = 1
    side = np.array([int(q in sides[c]) for q in qubits], dtype=np.uint8)
    nonc = h[[fc[f] != c for f in faces]].T
    assert np.array_equal((lam @ dc) % 2, h)
    assert not np.any((h @ h.T) % 2)
    assert rank2(h) == len(faces) == (len(qubits) - 1) // 2
    assert rank2(incidence) == len(vertices) - 1
    assert not np.any((incidence @ nonc) % 2)
    assert rank2(nonc.T) == len(qubits) - rank2(incidence)
    assert np.array_equal(incidence[-2], side)
    assert int(incidence[-2].sum()) == d and int(incidence[-1].sum()) == 1
    return h, incidence, edges


def distances(n, edges, weights):
    out = np.full((n, n), np.inf)
    np.fill_diagonal(out, 0)
    for (u, v), w in zip(edges, weights):
        out[u, v] = out[v, u] = min(out[u, v], w)
    for v in range(n):
        out = np.minimum(out, out[:, v, None] + out[None, v, :])
    return out


def shortest_path(n, edges, weights, source, target):
    """Heap search retaining edge IDs, including parallel and zero-cost edges."""
    adjacency = [[] for _ in range(n)]
    for eid, ((u, v), w) in enumerate(zip(edges, weights)):
        adjacency[u].append((v, w, eid))
        adjacency[v].append((u, w, eid))
    dist = [float("inf")] * n
    dist[source] = 0.
    parent = {}
    queue = [(0., source)]
    while queue:
        du, u = heapq.heappop(queue)
        if du != dist[u]:
            continue
        if u == target:
            path = []
            while u != source:
                u, eid = parent[u]
                path.append(eid)
            return du, path[::-1]
        for v, w, eid in adjacency[u]:
            if du + w < dist[v]:
                dist[v] = du + w
                parent[v] = (u, eid)
                heapq.heappush(queue, (dist[v], v))
    return float("inf"), None


def swim(n, edges, weights, radii):
    adjacency = [[] for _ in range(n)]
    for (u, v), w in zip(edges, weights):
        adjacency[u].append((v, w))
        adjacency[v].append((u, w))
    radius_max = max(radii, default=0)
    dist = radius_max - np.array(radii)
    queue = [(float(dist[v]), v) for v in range(n)]
    heapq.heapify(queue)
    while queue:
        du, u = heapq.heappop(queue)
        if du != dist[u]:
            continue
        for v, w in adjacency[u]:
            candidate = du + w
            if candidate < dist[v]:
                dist[v] = candidate
                heapq.heappush(queue, (candidate, v))
    heights = np.maximum(0, radius_max - dist)
    # Independent all-pairs ball union and explicit interval subdivision.
    metric = distances(n, edges, weights)
    expected = np.maximum(0, np.max(np.array(radii)[:, None] - metric, axis=0))
    assert np.allclose(heights, expected)
    bar = np.array([max(0, w - heights[u] - heights[v])
                    for (u, v), w in zip(edges, weights)])
    subedges, subweights = [], []
    next_node = n
    for (u, v), w in zip(edges, weights):
        breaks = sorted(set([0., float(w)] + [
            float(min(w, max(0, radii[s] - metric[s, u]))) for s in range(n)] + [
            float(w - min(w, max(0, radii[s] - metric[s, v]))) for s in range(n)]))
        nodes = [u] + list(range(next_node, next_node + max(0, len(breaks) - 2))) + [v]
        next_node += max(0, len(breaks) - 2)
        if w == 0:
            subedges.append((u, v)); subweights.append(0.)
            continue
        for j, (a, b) in enumerate(zip(breaks, breaks[1:])):
            midpoint = (a + b) / 2
            covered = any(min(metric[s, u] + midpoint, metric[s, v] + w - midpoint)
                          <= radii[s] + 1e-10 for s in range(n))
            subedges.append((nodes[j], nodes[j + 1]))
            subweights.append(0. if covered else b - a)
    quotient_distance = distances(next_node, subedges, subweights)[n - 2, n - 1]
    phi, path = shortest_path(n, edges, bar, n - 2, n - 1)
    expected_phi = distances(n, edges, bar)[-2, -1]
    assert np.isclose(phi, expected_phi) and np.isclose(phi, quotient_distance)
    if path is not None:
        boundary = np.zeros(n, dtype=np.uint8)
        seen = {n - 2}
        vertex = n - 2
        for eid in path:
            u, v = edges[eid]
            assert vertex in (u, v)
            vertex = v if vertex == u else u
            assert vertex not in seen
            seen.add(vertex)
            boundary[u] ^= 1
            boundary[v] ^= 1
        assert not np.any(boundary[:-2]) and np.all(boundary[-2:] == 1)
        assert abs(sum(bar[eid] for eid in path) - phi) < 1e-8
    else:
        assert np.isinf(phi)
    return phi, bar


def dual(n, edges, weights, syndrome):
    defects = list(np.flatnonzero(syndrome))
    radii = np.zeros(n)
    if not defects:
        return 0., radii
    metric = distances(n, edges, weights)
    boundary = np.min(metric[:, -2:], axis=1)
    sets = [[defects[j] for j in range(len(defects)) if (bits >> j) & 1]
            for bits in range(1, 1 << len(defects)) if bits.bit_count() % 2]
    membership = np.array([[int(u in s) for s in sets] for u in defects], dtype=float)
    constraints, limits = list(membership), [boundary[u] for u in defects]
    for i, j in combinations(range(len(defects)), 2):
        u, v = defects[i], defects[j]
        constraints.append(abs(membership[i] - membership[j]))
        limits.append(min(metric[u, v], boundary[u] + boundary[v]))
    result = linprog(-np.ones(len(sets)), A_ub=np.array(constraints),
                     b_ub=np.array(limits), bounds=(0, None), method="highs")
    assert result.success, result.message
    assert np.max(np.array(constraints) @ result.x - limits) < 1e-8
    radii[defects] = membership @ result.x
    return -result.fun, radii


def main():
    for d in (3, 5, 7, 9, 11):
        for c in COLORS:
            patch(d, c)
    instances = 0
    zero_dual_counterexample = False
    for c in COLORS:
        h, inc, edges = patch(3, c)
        n, m = inc.shape
        chains = np.array([[(bits >> j) & 1 for j in range(m)]
                           for bits in range(1 << m)], dtype=np.uint8)
        boundaries = (chains @ inc.T) % 2
        for z, bd in zip(chains, boundaries):
            if not np.any(bd[:-2]):
                assert not np.any((h @ z) % 2)
                assert rank2(np.vstack([h, z])) == rank2(h) + int(bd[-2])
        for weights in (np.ones(m), np.array([1., 2., 3., 1.5, .5, 4., 2.5]),
                        np.array([0., 2., 1., 3., 1., 0., 4.])):
            costs = chains @ weights
            for bits in range(1 << (n - 2)):
                syndrome = np.array([(bits >> j) & 1 for j in range(n - 2)])
                feasible = np.all(boundaries[:, :-2] == syndrome, axis=1)
                ids = np.flatnonzero(feasible)
                base = ids[np.argmin(costs[ids])]
                opposite = ids[boundaries[ids, -2] != boundaries[base, -2]]
                gap = min(costs[opposite]) - costs[base]
                value, radii = dual(n, edges, weights, syndrome)
                assert abs(value - costs[base]) < 1e-8
                phi, bar = swim(n, edges, weights, radii)
                _, path = shortest_path(n, edges, bar, n - 2, n - 1)
                witness = np.zeros(m, dtype=np.uint8)
                witness[path] = 1
                assert not np.any((h @ witness) % 2)
                assert rank2(np.vstack([h, witness])) == rank2(h) + 1
                assert abs(chains[base] @ bar) < 1e-8
                assert gap + 1e-8 >= phi
                logical = np.all(boundaries[:, :-2] == 0, axis=1) & (boundaries[:, -2] == 1)
                assert abs(min(chains[logical] @ bar) - phi) < 1e-8
                for i in ids:
                    assert costs[i] - chains[i] @ bar + 1e-8 >= value
                if np.all(weights == 1) and int(syndrome.sum()) == 1:
                    no_growth, _ = swim(n, edges, weights, np.zeros(n))
                    zero_dual_counterexample |= no_growth > gap
                instances += 1
        # Arbitrary geometric clusters: no growth, overlaps, both boundaries, partial lengths.
        for radii in (np.zeros(n), np.full(n, .3),
                      np.array([.7 * i for i in range(n)]), np.full(n, 20.)):
            swim(n, edges, np.arange(1, m + 1) / 2., radii)
    assert zero_dual_counterexample
    # Same component endpoints need not cover a costly alternative edge.
    triangle_edges = [(0, 1), (1, 2), (0, 2)]
    _, bar = swim(3, triangle_edges, [1., 1., 10.], [0., 1., 0.])
    assert np.allclose(bar, [0., 0., 10.])
    # Isolated terminals cannot become connected by contracting other components.
    phi, _ = swim(4, [(0, 2), (1, 3)], [1., 2.], [10., 10., 0., 0.])
    assert np.isinf(phi)
    # The d=3 red-face example quoted in the note: gap 1, no-growth swim 3.
    _, inc, edges = patch(3, "r")
    n, m = inc.shape
    syndrome = np.zeros(n - 2, dtype=np.uint8)
    syndrome[0] = 1  # Real face vertices precede primal-edge vertices.
    value, radii = dual(n, edges, np.ones(m), syndrome)
    assert np.isclose(value, 1.) and np.isclose(radii[0], 1.)
    assert np.isclose(swim(n, edges, np.ones(m), radii)[0], 1.)
    assert np.isclose(swim(n, edges, np.ones(m), np.zeros(n))[0], 3.)
    print("PASS: 15 family/color incidence and GF(2) rank checks (d=3,5,7,9,11).")
    print(f"PASS: {instances} exhaustive d=3 fiber/weight/color dual and gap checks.")
    print("PASS: all d=3 relative-chain logical classes; interval subdivision equivalence;")
    print("      partial coverage, merged/both-boundary clusters, original zero weights,")
    print("      same-cluster endpoint counterexample and nonoptimal-dual counterexample.")
    print("PASS: heap shortest paths and physical logical witnesses; disconnected terminals.")
    print("Finite checks support, but do not replace, the general manuscript proofs.")


if __name__ == "__main__":
    main()
