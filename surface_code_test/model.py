"""Read-only adapter for the upstream SO_example X-memory circuit and hard graph."""
from dataclasses import dataclass
from functools import lru_cache
import importlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import numpy as np
import pymatching
from pymatching.soft_output import SoftOutputConfig, PATH_GAP_VERSION
from scipy.sparse import csc_matrix
import sinter
import stim

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'external_libs/PyMatching/SO_example'
GROWTH_CONVENTION = 'sparse_blossom_final_defect_metric_balls_v1'


@lru_cache(maxsize=1)
def _example_modules():
    # Upstream uses sibling absolute imports; keep this compatibility shim local.
    sys.path.insert(0, str(EXAMPLE))
    try:
        modules = tuple(importlib.import_module(n) for n in ('circuit_gadget', 'so_sampler'))
        for module in modules:
            if Path(module.__file__).resolve().parent != EXAMPLE:
                raise ImportError('SO_example module name collision')
        return modules
    finally:
        sys.path.remove(str(EXAMPLE))


def build_circuit(distance: int, rounds: int, probability: float) -> stim.Circuit:
    """Build the exact example X-init → SE rounds → X-readout physical circuit.

    Args:
        distance: Odd rotated-code distance >=3.
        rounds: Positive count of SE_round calls, in addition to X_init's extraction.
        probability: Common gate/preparation/readout noise parameter in (0,.5).
    Returns:
        Closed X-memory Stim circuit; no output is written outside a temporary dir.
    Raises:
        ValueError: Unsupported parameters or unexpected observables/postselection.
    Notes:
        Noise placement and CNOT order come from the unmodified example, not
        Stim's generated circuit or color-code-stim's uniform-noise constructor.
    """
    if type(distance) is not int or distance < 3 or distance % 2 != 1:
        raise ValueError('distance must be odd and >=3')
    if type(rounds) is not int or rounds < 1 or not np.isfinite(probability) or not 0 < probability < .5:
        raise ValueError('positive rounds and noise in (0,.5) required')
    gadget, _ = _example_modules()
    name = f'sc{distance}'
    code = gadget.Rotated_surface_code(distance, name)
    code.logic_x_selection(0)
    code.logic_z_selection(0)
    with TemporaryDirectory(prefix='surface-memory-') as temporary:
        builder = gadget.Meta_Circuit([code], str(Path(temporary)/'memory.stim'), probability)
        builder.X_init(name, False)
        for _ in range(rounds):
            builder.SE_round(name, cleaness=False)
        builder.X_meas(name, False)
        circuit = builder.get_stim_circuit()
    if circuit.num_observables != 1 or any(len(c) != 3 for c in circuit.get_detector_coordinates().values()):
        raise ValueError('Expected one observable and no herald/postselection detectors')
    return circuit


class ComplementaryMatcher:
    """Force each logical class after a checked detector-row label gauge.

    Args:
        matcher: Frozen ordinary nonnegative graph, with one observable numbered 0.
    Raises:
        ValueError: Negative weights, explicit boundaries, or unbalanced internal labels.
    Notes:
        A spanning-forest potential removes internal labels. A gauged labelled
        half-edge becomes an edge to an additional constrained row.
        Its syndrome bit is the requested class XOR the potential-syndrome parity.
        Unlabelled half-edges remain boundary
        edges. This preserves every ordinary graph edge and its natural-log cost.
        The result is a minimum-representative gap, not a summed-likelihood LLR.
    """
    def __init__(self, matcher: pymatching.Matching):
        if matcher.boundary or matcher.num_fault_ids != 1:
            raise ValueError('One observable and implicit matching boundaries required')
        self.num_detectors = matcher.num_detectors
        self.edges = tuple(matcher.edges())
        adjacency = [[] for _ in range(self.num_detectors)]
        for u,v,data in self.edges:
            if not data['fault_ids'].issubset({0}):
                raise ValueError('Only observable zero is supported')
            if v is not None:
                label = int(bool(data['fault_ids']))
                adjacency[u].append((v,label)); adjacency[v].append((u,label))
        potential = np.full(self.num_detectors,-1,dtype=np.int8)
        components = np.full(self.num_detectors,-1,dtype=int)
        for root in range(self.num_detectors):
            if potential[root] >= 0:
                continue
            potential[root] = 0
            components[root] = root
            stack = [root]
            while stack:
                u = stack.pop()
                for v,label in adjacency[u]:
                    candidate = potential[u] ^ label
                    if potential[v] < 0:
                        potential[v] = candidate
                        components[v] = root
                        stack.append(v)
                    elif potential[v] != candidate:
                        raise ValueError('Internal logical labels are unbalanced')
        self.potential = potential.astype(np.uint8)
        rows, cols, weights, labels = [], [], [], []
        half_labels = {}
        for j, (u, v, data) in enumerate(self.edges):
            label = bool(data['fault_ids'])
            gauged = label ^ bool(self.potential[u]) ^ (bool(self.potential[v]) if v is not None else False)
            weight = float(data['weight'])
            if not np.isfinite(weight) or weight < 0:
                raise ValueError('Finite nonnegative weights required')
            rows.append(u); cols.append(j)
            if v is not None:
                rows.append(v); cols.append(j)
            elif gauged:
                rows.append(self.num_detectors); cols.append(j)
            if v is None:
                half_labels.setdefault(components[u],set()).add(gauged)
            weights.append(weight); labels.append(label)
        if not any(len(labels)==2 for labels in half_labels.values()):
            raise ValueError('No opposite logical class in this graph')
        self.incidence = csc_matrix((np.ones(len(rows),dtype=np.uint8),(rows,cols)),
                                   shape=(self.num_detectors+1,len(self.edges)))
        self.labels = np.asarray(labels,dtype=np.uint8)
        self.weights = np.asarray(weights)
        self.matcher = pymatching.Matching.from_check_matrix(
            self.incidence, weights=self.weights, faults_matrix=csc_matrix(self.labels[None,:]))

    def class_weights(self, detectors: np.ndarray) -> np.ndarray:
        """Return W0,W1, shape (shots,2), on the same syndromes in natural-log units.

        Raises ValueError for nonbinary/misaligned input; AssertionError if a forced
        solve returns the wrong logical bit. Matching uses backend quantized weights.
        """
        detectors = np.asarray(detectors)
        if detectors.ndim != 2 or detectors.shape[1] != self.num_detectors or not np.isin(detectors,[0,1]).all():
            raise ValueError('Expected binary (shots,num_detectors) array')
        result = np.empty((len(detectors),2))
        for bit in (0,1):
            forced = np.column_stack((detectors,(np.asarray(detectors,dtype=np.uint8) @ self.potential) % 2 ^ bit))
            prediction, weights = self.matcher.decode_batch(forced,return_weights=True)
            if not np.all(prediction[:,0] == bit):
                raise AssertionError('Forced matching logical class mismatch')
            result[:,bit] = weights
        return result


@dataclass(frozen=True)
class SurfaceResult:
    """Per-shot vectors: ordinary prediction and natural-log weights and three scores.

    class_weights has shape (shots,2), ordered logical class 0 then 1.
    All other arrays have shape (shots,). All scores use the ordinary prediction.
    Path gap is signed global_subtraction_v1; correction weight is the original
    floating edge sum, separately from the backend quantized solution weight.
    """
    prediction: np.ndarray
    solution_weight: np.ndarray
    swim_distance: np.ndarray
    complementary_gap: np.ndarray
    class_weights: np.ndarray
    path_gap: np.ndarray
    path_gap_residual_distance: np.ndarray
    path_gap_correction_weight: np.ndarray


class SurfaceDecoder:
    """Use the example hard graph and split-X-boundary topology with generic SO.

    Args:
        circuit: The closed X-memory circuit returned by build_circuit.
    Raises:
        ValueError: Unsupported half-edge/logical geometry or topology.
    Notes:
        Generic final-defect metric balls replace the example's historical SO API.
        Hard predictions/weights are checked exactly against SO-off each batch.
        Scores remain unrounded natural-log costs and growth is uncertified.
    """
    def __init__(self, circuit: stim.Circuit):
        self.circuit = circuit
        _, sampler = _example_modules()
        self.matcher = sampler.construct_decoder(sinter.Task(circuit=circuit),basis='X')
        self.complementary = ComplementaryMatcher(self.matcher)
        n = self.matcher.num_detectors
        if n != circuit.num_detectors:
            raise ValueError('Example graph and physical detector dimensions differ')
        coords = circuit.get_detector_coordinates()
        edges, boundary_labels = [], {0:set(),1:set()}
        for j,(u,v,data) in enumerate(self.matcher.edges()):
            if v is None:
                x,y,_ = coords[u]
                if (x-y) % 2 != 0:
                    if bool(data['fault_ids']) ^ bool(self.complementary.potential[u]):
                        raise ValueError('Z-check half-edge changes gauged X-memory logical bit')
                    continue  # Same exclusion as SO_example X-boundary metric.
                if y == 0:
                    raise ValueError('Cannot classify example X-boundary half-edge')
                side = int(y > 0)
                boundary_labels[side].add(int(bool(data['fault_ids']) ^ bool(self.complementary.potential[u])))
                v = n+side
            edges.append((j,u,v,float(data['weight'])))
        if sorted(boundary_labels.values(),key=str) != [{0},{1}]:
            raise ValueError('Split X boundaries must have distinct logical labels')
        self.topology = SoftOutputConfig(tuple(range(n))+(-1,-1),tuple(edges),((n,n+1),))
        self.matcher.configure_soft_output(self.topology)
        self.diagnostics = dict(detectors=n,hard_edges=len(self.complementary.edges),
            analysis_edges=len(edges),path_gap_metric_version=PATH_GAP_VERSION,boundary_labels={str(k):list(v) for k,v in boundary_labels.items()},
            observable_count=1,swim_bound_certified=False,growth_convention=GROWTH_CONVENTION)

    def decode(self, detectors: np.ndarray) -> SurfaceResult:
        """Return paired scores and verify ordinary hard invariance for every shot.

        Args: detectors: Binary physical sample, shape (shots,num_detectors).
        Returns: SurfaceResult, costs in natural-log units; no sample/discard occurs.
        Raises: ValueError/AssertionError for invalid input or any failed check.
        """
        prediction, weights = self.matcher.decode_batch(detectors,return_weights=True)
        soft = self.matcher.decode_batch_with_soft_output(detectors)
        np.testing.assert_array_equal(soft.predictions,prediction)
        np.testing.assert_array_equal(soft.solution_weights,weights)
        path = self.matcher.decode_batch_with_path_gap(detectors)
        np.testing.assert_array_equal(path.predictions,prediction)
        np.testing.assert_array_equal(path.solution_weights,weights)
        if not np.isfinite(path.path_gaps).all():
            raise ValueError('Nonfinite path gaps')
        classes = self.complementary.class_weights(detectors)
        # Both graphs have identical edge weights and the same quantization scale.
        np.testing.assert_allclose(classes.min(axis=1),weights,rtol=1e-10,atol=1e-8)
        np.testing.assert_allclose(classes[np.arange(len(classes)),prediction[:,0]],weights,rtol=1e-10,atol=1e-8)
        swim = soft.soft_outputs[:,0]
        gap = np.abs(classes[:,1]-classes[:,0])
        if not np.isfinite(swim).all() or (swim < 0).any():
            raise ValueError('Invalid swim distances')
        return SurfaceResult(prediction[:,0].astype(bool),weights,swim,gap,classes,
            path.path_gaps[:,0],path.residual_distances[:,0],path.correction_weights)


@lru_cache(maxsize=3)
def model(distance: int, rounds: int, probability: float) -> SurfaceDecoder:
    """Cache up to three immutable circuit/decoder configurations per worker."""
    return SurfaceDecoder(build_circuit(distance,rounds,probability))
