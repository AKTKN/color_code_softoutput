"""Original-prior circuit SWIM for generated concatenated-matching candidates."""

import numpy as np

from ..circuit_level.decoder import Stage2GrowthBackend


class CircuitCandidateSwim:
    """Score candidate stage-2 syndromes in a closed triangular memory DEM."""

    def __init__(self, code):
        if (code.circuit_type != "tri" or code.temp_bdry_type != "Z"
                or code.rounds != code.d or code.comparative_decoding
                or code.circuit.num_observables != 1
                or tuple(code.cnot_schedule) != (2, 3, 6, 5, 4, 1, 3, 4, 7, 6, 5, 2)):
            raise ValueError("circuit SWIM requires closed d-round triangular Z memory with tri_optimal schedule")
        self.code = code
        self.backends = {color: Stage2GrowthBackend(code.dem_manager, color)
                         for color in "rgb"}
        if any(not backend.topology.class_exists for backend in self.backends.values()):
            raise ValueError("circuit stage-2 opposite logical class is absent")

    def score(self, detectors, prediction, extra):
        """Return the same-hard-logical-class minimum across generated candidates."""
        shots = np.asarray(detectors, dtype=bool)
        mapped = np.asarray(extra["candidate_original_corrections"], dtype=bool)
        hypotheses = extra["candidate_stage1_hypotheses"]
        targets = tuple(extra["candidate_target_colors"])
        valid = np.asarray(extra.get("candidate_valid", np.ones(mapped.shape[:3], dtype=bool)),
                           dtype=bool)
        if (mapped.ndim != 4 or mapped.shape[2] != len(shots)
                or mapped.shape[3] != self.code.H.shape[1]
                or valid.shape != mapped.shape[:3]
                or len(targets) != mapped.shape[1]
                or len(hypotheses) != mapped.shape[0]):
            raise ValueError("Invalid candidate tensors for circuit SWIM")
        scores = np.full(valid.shape, np.inf, dtype=float)
        for logical_class in range(mapped.shape[0]):
            if len(hypotheses[logical_class]) != mapped.shape[1]:
                raise ValueError("Missing candidate stage-1 hypotheses")
            for slot, color in enumerate(targets):
                active = valid[logical_class, slot]
                if not np.any(active):
                    continue
                if color not in self.backends or hypotheses[logical_class][slot] is None:
                    raise ValueError("Missing supported candidate stage-1 hypothesis")
                stage1 = np.asarray(hypotheses[logical_class][slot], dtype=bool)
                if stage1.shape[0] != len(shots):
                    raise ValueError("Candidate stage-1 shot count differs")
                branch = self.backends[color].decode_hypotheses(
                    shots[active], stage1[active])
                scores[logical_class, slot, active] = [r.phi for r in branch.results]
        flat = mapped.reshape(-1, mapped.shape[-1])
        observable = np.asarray(
            (flat.astype(np.uint8) @ self.code.obs_matrix.T) % 2, dtype=bool,
        ).reshape(mapped.shape[:3] + (self.code.circuit.num_observables,))
        selected = np.asarray(prediction, dtype=bool).reshape(len(shots), -1)
        if selected.shape != (len(shots), self.code.circuit.num_observables):
            raise ValueError("Hard prediction shape differs from candidate observable")
        same = np.all(observable == selected[None, None, :, :], axis=-1)
        output = np.min(np.where(valid & same, scores, np.inf), axis=(0, 1))
        if output.shape != (len(shots),) or not np.isfinite(output).all():
            raise ValueError("No finite same-logical-class circuit SWIM candidate")
        return output
