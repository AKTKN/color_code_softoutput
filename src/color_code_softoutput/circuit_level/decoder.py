"""Read-only circuit swim adapter using the existing generic growth export.

The public ordinary decoder remains the source of every hard return value.
Frozen public matrices are replayed to observe stage-2 growth. This deliberate
extra decoding cost avoids monkey-patching or depending on private decoder state.
"""
from dataclasses import dataclass
from typing import Any
import numpy as np
from numpy.typing import ArrayLike
import pymatching
from color_code_stim import ColorCode
from color_code_stim.dem_utils.dem_manager import DemManager
from color_code_stim.dem_utils.dem_decomp import DemDecomp
from pymatching.soft_output import SoftOutputConfig
from .coverage import GROWTH_CONVENTION, COVERAGE_CONVENTION, residual_weights
from .dem_adapter import adapt_stage2
from .logical_topology import preprocess_topology
from .model import CircuitLevelSwimResult, RowRole
from .swim import compute_circuit_level_swim
from .validation import validate_correction, validate_hard_invariance


@dataclass(frozen=True)
class BranchBatch:
    """Observed branch outputs; bit arrays use (shots, columns/rows), costs log odds.

    Results and residual_weights have one entry per shot. radii columns follow
    active H2 rows followed by the artificial boundary, whose radius is zero.
    labelled_correction_weights are separate from quantized hard solution_weights.
    """
    stage1_predictions: np.ndarray
    syndromes: np.ndarray
    corrections: np.ndarray
    solution_weights: np.ndarray
    labelled_correction_weights: np.ndarray
    radii: np.ndarray
    residual_weights: np.ndarray
    results: tuple[CircuitLevelSwimResult, ...]


class Stage2GrowthBackend:
    """Cache a replay of the actual frozen H1/H2 path for one ordinary branch.

    Args:
        manager: Public closed triangular memory DEM manager.
        color: 'r', 'g' or 'b'.
    Raises:
        ValueError/NotImplementedError: Adapter/topology or weight gates fail.
    Notes:
        No changes are made to manager matrices, hard merge rules or tie policy.
        The configured (b_star,b_star) pair only enables the existing radius API;
        its identically-zero distance is discarded, never used as a logical score.
    """
    def __init__(self, manager: DemManager, color: str) -> None:
        self.graph = adapt_stage2(manager, color)
        self.topology = preprocess_topology(self.graph)
        decomp = manager.dems_decomposed[color]
        self._H1, self._H2 = (x.copy() for x in decomp.Hs)
        self._p1, self._p2 = (x.copy() for x in decomp.probs)
        self._L2 = decomp.obs_matrix_stage2.copy()
        self._source_map = decomp.error_map_matrices[1].copy()
        self._row_metadata = decomp.stage2_rows
        self._edge_metadata = decomp.stage2_edges
        self._keep1 = self._H1.getnnz(axis=1) > 0
        self._matcher1 = pymatching.Matching.from_check_matrix(
            self._H1[self._keep1, :], weights=np.log((1-self._p1)/self._p1))
        self._matcher2 = pymatching.Matching.from_check_matrix(self._H2, weights=self.graph.weights)
        self.growth_config = SoftOutputConfig(
            self.graph.active_rows + (-1,),
            tuple((e.column_id, *e.endpoints, e.weight) for e in self.graph.mechanisms),
            ((self.graph.b_star, self.graph.b_star),))
        self._matcher2.configure_soft_output(self.growth_config)
        self._num_detectors = manager.circuit.num_detectors

    def matches(self, decomp: DemDecomp) -> bool:
        """Return whether current public H1/H2 and probabilities match frozen inputs.

        Args: decomp: Current branch decomposition.
        Returns: Exact equality, including ordering and dimensions; no tolerance.
        """
        return (all(a.shape == b.shape and (a != b).nnz == 0 for a, b in (
                    (self._H1,decomp.Hs[0]),(self._H2,decomp.Hs[1]),
                    (self._L2,decomp.obs_matrix_stage2),(self._source_map,decomp.error_map_matrices[1])))
                and all(np.array_equal(a,b) for a,b in zip((self._p1,self._p2),decomp.probs))
                and self._row_metadata == decomp.stage2_rows and self._edge_metadata == decomp.stage2_edges)

    def decode(self, detector_outcomes: ArrayLike, *, return_witness: bool = False) -> BranchBatch:
        """Replay unchanged two-stage matrices, read radii and compute residual swim.

        Args:
            detector_outcomes: Binary array (shots, physical detectors).
            return_witness: Include verified original-column witnesses per shot.
        Returns:
            BranchBatch, with hard and geometric costs explicitly separate.
        Raises:
            ValueError: Invalid inputs, stage-1/2 feasibility, unavailable growth,
                or nonzero growth at a nonsyndrome vertex.
        """
        shots = np.asarray(detector_outcomes)
        if shots.ndim != 2 or shots.shape[1] != self._num_detectors or not np.isin(shots, [0, 1]).all():
            raise ValueError("Binary (shots, physical detectors) array required")
        stage1 = self._matcher1.decode_batch(shots[:, self._keep1])
        return self.decode_hypotheses(shots, stage1, return_witness=return_witness)

    def decode_hypotheses(self, detector_outcomes: ArrayLike,
                          stage1_hypotheses: ArrayLike, *,
                          return_witness: bool = False) -> BranchBatch:
        """Score supplied stage-1 candidates on this frozen original-prior H2.

        The supplied hypotheses may have been generated with another prior.
        Stage-2 matching, growth, residual edge weights and topology all use
        the unchanged base decomposition held by this backend.
        """
        shots = np.asarray(detector_outcomes)
        stage1 = np.asarray(stage1_hypotheses, dtype=np.uint8)
        if (shots.ndim != 2 or shots.shape[1] != self._num_detectors
                or not np.isin(shots, [0, 1]).all()
                or stage1.shape != (len(shots), self._H1.shape[1])
                or not np.isin(stage1, [0, 1]).all()):
            raise ValueError("Aligned binary detectors and stage-1 hypotheses required")
        if not np.array_equal(stage1.astype(np.uint8) @ self._H1[self._keep1, :].T % 2,
                              shots[:, self._keep1]):
            raise ValueError("Stage-1 correction violates restricted syndrome")
        syndromes = np.zeros((len(shots), self.graph.original_shape[0]), dtype=np.uint8)
        # Metadata defines row roles/source IDs, never detector-index ranges.
        for row in self.graph.rows:
            if row.role == RowRole.PHYSICAL:
                syndromes[:, row.row_id] = shots[:, row.source_id]
            elif row.role == RowRole.VIRTUAL:
                syndromes[:, row.row_id] = stage1[:, row.source_id]
        growth = self._matcher2.decode_batch_with_soft_output(syndromes, include_radii=True)
        validate_correction(self.graph, growth.predictions, syndromes)
        if growth.radii is None or growth.radii.shape != (len(shots), self.graph.num_vertices):
            raise ValueError("Growth unavailable or incorrectly mapped")
        real_syndrome = syndromes[:, self.graph.active_rows]
        if np.any(growth.radii[:, :-1][real_syndrome == 0]) or np.any(growth.radii[:, -1]):
            raise ValueError("Growth center is not an original stage-2 defect")
        residuals = np.empty((len(shots), len(self.graph.mechanisms)))
        results = []
        for i, radii in enumerate(growth.radii):
            residuals[i] = residual_weights(self.graph, radii)
            results.append(compute_circuit_level_swim(self.topology, residuals[i], return_witness=return_witness))
        return BranchBatch(stage1, syndromes, growth.predictions, growth.solution_weights,
                           growth.predictions @ np.asarray(self.graph.weights), growth.radii,
                           residuals, tuple(results))


class CircuitLevelDecoder:
    """Attach per-color swim to the unchanged ordinary closed-memory hard result.

    Args:
        code: ColorCode with triangular Z memory, rounds=d, canonical tri_optimal
            schedule, ordinary decoding and one measured logical observable.
    Raises:
        NotImplementedError: Unsupported memory configuration or open boundary.
        ValueError: Missing opposite class in the standard memory model.
    Notes:
        A complete ordinary decode plus a frozen-matrix replay is performed.
        This is a correctness-first integration, with no negligible-overhead claim.
    """
    def __init__(self, code: ColorCode) -> None:
        if (code.circuit_type != "tri" or code.temp_bdry_type != "Z" or code.rounds != code.d
                or code.comparative_decoding or code.circuit.num_observables != 1
                or tuple(code.cnot_schedule) != (2,3,6,5,4,1,3,4,7,6,5,2)):
            raise NotImplementedError("Requires closed d-round triangular Z memory with tri_optimal schedule")
        self.code = code
        self._circuit_text = str(code.circuit)
        self.backends = {c: Stage2GrowthBackend(code.dem_manager, c) for c in "rgb"}
        if any(not b.topology.class_exists for b in self.backends.values()):
            raise ValueError("Standard measured-sector model has no opposite class; investigate")

    def diagnostics(self) -> list[dict]:
        """Return JSON-ready static graph gates/counts, with no sampling.

        Returns: One record per color; obstruction count means forest inconsistencies.
        """
        records = []
        for c, backend in self.backends.items():
            g, top = backend.graph, backend.topology
            records.append(dict(distance=self.code.d, rounds=self.code.rounds, color=c,
                class_exists=top.class_exists, balance_passed=top.balance_passed, method=top.method.value,
                vertices=g.num_vertices, mechanisms=len(g.mechanisms),
                half_edges=sum(len(e.endpoint_rows) == 1 for e in g.mechanisms),
                zero_detector_loops=sum(not e.endpoint_rows for e in g.mechanisms),
                internal_odd_cycle_obstructions=len(top.odd_cycle_obstructions), model_id=g.model_id))
        return records

    def decode(self, detector_outcomes: ArrayLike, *, compute_swim_distance: bool = True,
               return_witness: bool = False, include_debug: bool = False) -> tuple[np.ndarray, dict[str, Any]]:
        """Return ordinary predictions/full output with optional circuit swim fields.

        Args:
            detector_outcomes: Binary (shots, detectors) or one detector vector.
            compute_swim_distance: False delegates directly to ordinary hard decoding.
            return_witness: Return per-shot original-mechanism witnesses if enabled.
            include_debug: Include branch syndromes/corrections/radii/residuals.
        Returns:
            (prediction, extra), with (shots,3) per-color weights/scores and selected
            score from ordinary best_colors. All hard products remain unchanged.
        Raises:
            ValueError: Stale input model, invalid inputs or any hard-output mismatch.
        """
        shots = np.asarray(detector_outcomes)
        if shots.ndim == 1:
            shots = shots[None, :]
        if shots.ndim != 2 or shots.shape[1] != self.code.circuit.num_detectors or not np.isin(shots,[0,1]).all():
            raise ValueError("Binary detector array with original physical detector count required")
        if str(self.code.circuit) != self._circuit_text or any(
                not b.matches(self.code.dems_decomposed[c]) for c, b in self.backends.items()):
            raise ValueError("Frozen circuit/decomposition changed; construct a new adapter")
        if len(shots):
            prediction, extra = self.code.decode(shots, full_output=True, check_validity=True)
        else:
            prediction = np.empty(0, dtype=bool)
            extra = dict(weights=np.empty(0), best_colors=np.empty(0,dtype=np.uint8),
                         error_preds=np.empty((0,self.code.H.shape[1]),dtype=bool), validity=np.empty(0,dtype=bool))
        if not compute_swim_distance:
            return prediction, extra
        branches = {c: b.decode(shots, return_witness=return_witness) for c, b in self.backends.items()}
        weights = np.column_stack([branches[c].solution_weights for c in "rgb"])
        scores = np.column_stack([[r.phi for r in branches[c].results] for c in "rgb"])
        chosen = extra["best_colors"]
        replay_colors = np.argmin(weights, axis=1)
        replay_errors = np.empty_like(extra["error_preds"])
        for i, c in enumerate("rgb"):
            mapped = self.code.dems_decomposed[c].map_errors_to_org_dem(branches[c].corrections, stage=2)
            mask = replay_colors == i
            replay_errors[mask] = mapped[mask]
        replay_pred = (replay_errors.astype(np.uint8) @ self.code.obs_matrix.T % 2).astype(bool).ravel()
        validate_hard_invariance(prediction, extra, replay_pred, dict(
            weights=weights[np.arange(len(shots)), replay_colors], best_colors=replay_colors, error_preds=replay_errors))
        if not np.all(extra["validity"]):
            raise ValueError("Ordinary hard correction has invalid physical syndrome")
        extra.update(color_order=tuple("rgb"), stage2_weights_by_color=weights,
            swim_distances_by_color=scores, selected_swim_distance=scores[np.arange(len(shots)),chosen],
            swim_methods_by_color=tuple(self.backends[c].topology.method.value for c in "rgb"),
            balance_passed_by_color=tuple(self.backends[c].topology.balance_passed for c in "rgb"),
            class_exists_by_color=tuple(self.backends[c].topology.class_exists for c in "rgb"),
            swim_bound_certified=False, swim_growth_convention=GROWTH_CONVENTION,
            swim_coverage_convention=COVERAGE_CONVENTION, hard_invariance_checked_shots=len(shots))
        if return_witness:
            extra["witnesses_by_color"] = {c: tuple(r.witness for r in branches[c].results) for c in "rgb"}
        if include_debug:
            extra["branches"] = branches
        return prediction, extra
