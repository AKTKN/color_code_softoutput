"""M1 regression of the included surface example on frozen M0 shots."""
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
import pymatching
import sinter
import stim
from pymatching.soft_output import SoftOutputConfig

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'external_libs/PyMatching/SO_example'))
from so_sampler import construct_decoder

fixture = np.load(ROOT / 'implementation_artifacts/baseline/surface_so.npz')
circuit = stim.Circuit.from_file(ROOT / 'implementation_artifacts/baseline/sc5_10_SE_rds.stim')
attachments, pairs = {}, []
old_attach = pymatching.Matching.add_boundary_edge_SO
old_pair = pymatching.Matching.add_cycle_endpoints_pair_SO

def attach(self, u, v):
    attachments[u] = v
    return old_attach(self, u, v)

def pair(self, u, v):
    pairs.append((u,v))
    return old_pair(self, u, v)

with patch.object(pymatching.Matching, 'add_boundary_edge_SO', attach), patch.object(
        pymatching.Matching, 'add_cycle_endpoints_pair_SO', pair):
    matcher = construct_decoder(sinter.Task(circuit=circuit), basis='X')
shots = fixture['detectors']
pred, old_soft = matcher.decode_batch_soft_output(shots, return_weights=True)
np.testing.assert_array_equal(pred, fixture['predictions'])
np.testing.assert_array_equal(old_soft, fixture['soft_outputs'])
pred, weights = matcher.decode_batch(shots, return_weights=True)
edges = []
for i, (u,v,a) in enumerate(matcher.edges()):
    if v is None:
        if u not in attachments:
            continue
        v = attachments[u]
    edges.append((i,u,v,a['weight']))
n = max(max(p) for p in pairs) + 1
matcher.configure_soft_output(SoftOutputConfig(
    tuple(range(matcher.num_nodes)) + (-1,) * (n-matcher.num_nodes), edges, pairs))
result = matcher.decode_batch_with_soft_output(shots)
np.testing.assert_array_equal(result.predictions, pred)
np.testing.assert_array_equal(result.solution_weights, weights)
assert np.isfinite(result.soft_outputs).all()
print('Surface example: legacy fixture, hard prediction, ordinary weight, finite separate SO passed (64 shots).')
