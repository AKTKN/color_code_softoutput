"""Finite theorem/counterexample checks. No sampling or decoder source changes.
Run: conda run -n color_code_so python notes/support/check_circuit_theory.py
"""
import heapq
import itertools
import math
import random
import numpy as np
import stim
from check_phase1 import patch, rank2
from color_code_stim import ColorCode
from color_code_stim.noise_model import NoiseModel
from color_code_stim.dem_utils.dem_decomp import DemDecomp


def shortest(n, edges, start, end):
    adj = [[] for _ in range(n)]
    for i, (u, v, w, _) in enumerate(edges):
        adj[u].append((v, w, i)); adj[v].append((u, w, i))
    dist = [math.inf] * n; dist[start] = 0
    prev = {}; heap = [(0, start)]; done = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in done: continue
        done.add(u)
        if u == end: break
        for v, w, i in adj[u]:
            if v not in done and d + w < dist[v]:
                dist[v] = d + w; prev[v] = (u, i)
                heapq.heappush(heap, (dist[v], v))
    path = []
    if math.isfinite(dist[end]):
        v = end
        while v != start:
            v, i = prev[v]; path.append(i)
    return dist[end], path


def cover(n, edges):
    lifted = [(2*u+a, 2*v+(a ^ l), w, l)
              for u, v, w, l in edges for a in (0, 1)]
    best, witness = math.inf, []
    for u in range(n):
        value, path = shortest(2*n, lifted, 2*u, 2*u+1)
        if value < best:
            parity = set()
            for i in path:
                source = i // 2
                if source in parity: parity.remove(source)
                else: parity.add(source)
            best, witness = value, sorted(parity)
    if math.isfinite(best):
        check(n, edges, witness, best)
    return best, witness


def check(n, edges, witness, cost):
    syndrome = [0] * n; logical = 0; weight = 0
    for i in witness:
        u, v, w, l = edges[i]
        syndrome[u] ^= 1; syndrome[v] ^= 1; logical ^= l; weight += w
    assert not any(syndrome) and logical == 1 and weight == cost


def exhaustive(n, edges):
    best = math.inf
    # Gray-code traversal independently evaluates all binary chains.
    syn = [0] * n; logical = 0; cost = 0; previous = 0
    for k in range(1, 1 << len(edges)):
        gray = k ^ (k >> 1); changed = gray ^ previous
        i = changed.bit_length() - 1
        u, v, w, l = edges[i]
        syn[u] ^= 1; syn[v] ^= 1; logical ^= l
        cost += w if gray & changed else -w
        if logical and not any(syn): best = min(best, cost)
        previous = gray
    return best


def cut(n, edges):
    # Last base vertex is the unique artificial boundary.
    b = n - 1; potential = [None] * b
    adj = [[] for _ in range(b)]
    for u, v, _, l in edges:
        if u != b and v != b:
            adj[u].append((v, l)); adj[v].append((u, l))
    for root in range(b):
        if potential[root] is not None: continue
        potential[root] = 0; stack = [root]
        while stack:
            u = stack.pop()
            for v, l in adj[u]:
                want = potential[u] ^ l
                if potential[v] is None:
                    potential[v] = want; stack.append(v)
                elif potential[v] != want: return None
    potential.append(0); out = []
    for u, v, w, l in edges:
        l ^= potential[u] ^ potential[v]
        if u == b and v == b: out.append((b, b+l, w, l))
        elif u == b: out.append((b+l, v, w, l))
        elif v == b: out.append((u, b+l, w, l))
        else:
            assert l == 0
            out.append((u, v, w, l))
    value, witness = shortest(n+1, out, b, b+1)
    if math.isfinite(value): check(n, edges, witness, value)
    return value


def residual(n, edges, radii):
    # Floyd-Warshall oracle, independent of the note's heap coverage algorithm.
    dist = np.full((n,n), np.inf); np.fill_diagonal(dist, 0)
    for u,v,w,_ in edges:
        dist[u,v] = min(dist[u,v],w); dist[v,u] = min(dist[v,u],w)
    for k in range(n): dist = np.minimum(dist, dist[:,k,None]+dist[None,k,:])
    h = np.maximum(0, np.max(np.asarray(radii)[:,None]-dist,axis=0))
    return [(u,v,int(max(0,w-h[u]-h[v])),l) for u,v,w,l in edges]


def model_edges(decomp):
    H = decomp.Hs[1].toarray().astype(np.uint8)
    L = decomp.obs_matrix_stage2.toarray().astype(np.uint8)
    active = np.any(H,axis=1); H = H[active]
    n = len(H)+1; b = n-1; edges = []
    for j in range(H.shape[1]):
        endpoints = list(np.flatnonzero(H[:,j])); assert len(endpoints) <= 2
        endpoints += [b] * (2-len(endpoints))
        edges.append((*endpoints,1,int(L[0,j]) if len(L) else 0))
    return n, edges, H, L


def main():
    rng = random.Random(20260912); balanced = 0
    for _ in range(400):
        n = rng.randrange(1,7)
        edges = [(rng.randrange(n),rng.randrange(n),rng.randrange(7),rng.randrange(2))
                 for _ in range(rng.randrange(1,11))]
        expected = exhaustive(n,edges)
        assert cover(n,edges)[0] == expected
        result = cut(n,edges)
        if result is not None:
            balanced += 1; assert result == expected
        gauge = [rng.randrange(2) for _ in range(n-1)]+[0]
        changed = [(u,v,w,l ^ gauge[u] ^ gauge[v]) for u,v,w,l in edges]
        assert cover(n,changed)[0] == expected
        radii = [rng.randrange(5) for _ in range(n-1)]+[0]
        reduced = residual(n,edges,radii)
        assert cover(n,reduced)[0] == exhaustive(n,reduced)
    print(f'PASS 400 exhaustive random labelled multigraphs; {balanced} valid cuts; gauges and residuals')
    triangle = [(0,1,1,1),(1,2,1,0),(2,0,1,0),(2,3,10,0)]
    assert cover(4,triangle)[0] == 3 and cut(4,triangle) is None
    lifted = [(2*u+a,2*v+(a^l),w,l) for u,v,w,l in triangle for a in (0,1)]
    assert shortest(8,lifted,6,7)[0] == 23
    assert cover(2,[(0,1,0,0),(0,1,0,1)])[0] == 0
    assert cover(3,[(0,1,1,1)])[0] == math.inf
    print('PASS counterexamples: boundary-source 23 vs 3; zero odd parallel pair; unmatched-sheet endpoints')
    for d,c in itertools.product((3,5,7),('r','g','b')):
        # patch returns physical geometry and incidence, independent of decoder.
        h, incidence, ep = patch(d,c)
        side = incidence[-2]
        b0,b1 = len(incidence)-2,len(incidence)-1
        edges = [(min(u,b0),min(v,b0),1,int(side[i])) for i,(u,v) in enumerate(ep)]
        assert cover(b0+1,edges)[0] == d and cut(b0+1,edges) == d
    print('PASS Phase-1 all-color graph reduction at d=3,5,7 (unit costs)')
    for T in (1,2):
        cc = ColorCode(d=3, rounds=T, circuit_type='tri', cnot_schedule='tri_optimal',
                       noise_model=NoiseModel(meas_data=.02,meas_anc_Z=.02))
        for c in ('r','g','b'):
            decomp = cc.dem_manager.dems_decomposed[c]
            n,edges,H,L = model_edges(decomp)
            assert len(edges) <= 20
            assert rank2(np.vstack((H,L))) == rank2(H)+1
            assert exhaustive(n,edges) == cover(n,edges)[0]
            assert len(decomp[1].shortest_graphlike_error()) == cover(n,edges)[0]
            reduced = residual(n,[(u,v,1+i%5,l) for i,(u,v,_,l) in enumerate(edges)],
                               [1]*(n-1)+[0])
            assert exhaustive(n,reduced) == cover(n,reduced)[0]
            result = cut(n,reduced)
            if result is not None: assert result == cover(n,reduced)[0]
            J = decomp.error_map_matrices[1].toarray().astype(np.uint8).T
            assert np.array_equal((cc.dem_manager.obs_matrix.toarray() @ J)%2,
                                  decomp.obs_matrix_stage2.toarray())
            print(f'PASS d=3 T={T} color={c}: all {1<<len(edges)} subsets, {len(edges)} mechanisms, Stim, frame map; cut={result}')
    # A matrix-only circuit-noise audit: not exhaustive and no sampled shots.
    cc = ColorCode(d=3, rounds=2, circuit_type='tri', cnot_schedule='tri_optimal',
                   noise_model=NoiseModel.uniform_circuit_noise(.001))
    for c in ('r','g','b'):
        n,edges,H,L = model_edges(cc.dem_manager.dems_decomposed[c])
        assert cut(n,edges) == cover(n,edges)[0] == 2
        print(f'PASS full circuit-noise matrix audit d=3 T=2 color={c}: {n} vertices, {len(edges)} mechanisms, cut/cover=2; not exhaustive')
    duplicate = stim.DetectorErrorModel('error(0.1) D0 L0\nerror(0.2) D0 L0\ndetector(0,0,0,2,0) D0')
    dd = DemDecomp(org_dem=duplicate,color='r')
    assert np.allclose(dd.probs[1],[.2])
    assert not np.isclose(dd.probs[1][0],.1+.2-2*.1*.2)
    filtered = stim.DetectorErrorModel('error(0.1) D0 D1\nerror(0.2) D0 D1 D2\ndetector(0,0,0,2,1) D0\ndetector(0,0,0,2,0) D1\ndetector(1,0,0,2,0) D2')
    dd = DemDecomp(org_dem=filtered,color='r')
    assert np.allclose(dd.probs[0],[.1])
    print('PASS source discrepancy reproducers: duplicate probability .2 vs .26; stage-1 prefilter .1 vs .26')
    print('No Monte Carlo, production modifications, or production dual certification performed.')


if __name__ == '__main__': main()
