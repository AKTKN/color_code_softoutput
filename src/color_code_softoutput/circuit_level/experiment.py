"""Small d-round uniform-noise configuration, paired worker and storage contract."""
from dataclasses import asdict, dataclass
from functools import lru_cache
from collections.abc import Iterator
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
from color_code_stim import ColorCode, NoiseModel
from ..simulation.config import BatchTask, PROJECT_ROOT, batch_seed
from ..simulation.pairing import validate_pairing
from ..simulation.storage import SHOT_SCHEMA, validate_shots
from .decoder import CircuitLevelDecoder

NOISE_MODEL_NAME = "uniform_circuit_noise"
COMPARATIVE_COLORS = tuple("rgb")


@dataclass(frozen=True)
class CircuitLevelMemoryConfig:
    """Bounded implementation-validation memory grid, never a threshold sweep.

    Args:
        distances: Unique subset of (3,5,7); rounds always equals distance.
        physical_error_rate: Single uniform circuit-noise probability, default .003.
        shots_per_point, batch_size, num_workers: Positive shot/process counts.
        master_seed: Nonnegative SeedSequence seed.
        output_root: Parent of timestamped result directories.
        verbose: Emit progress when True.
    Raises: ValueError: Unsupported distance, probability or infrastructure setting.
    Notes: .003 is an implementation-validation point, not a reproduced paper point.
    """
    distances: tuple[int, ...] = (3,5,7)
    physical_error_rate: float = .003
    shots_per_point: int = 2000
    batch_size: int = 250
    num_workers: int = 3
    master_seed: int = 20260916
    output_root: Path = PROJECT_ROOT / "results"
    verbose: bool = True

    def __post_init__(self):
        object.__setattr__(self, 'distances', tuple(self.distances))
        object.__setattr__(self, 'output_root', Path(self.output_root))
        if (not self.distances or len(set(self.distances)) != len(self.distances)
                or any(type(d) is not int or d not in (3,5,7) for d in self.distances)):
            raise ValueError("Validation distances must be a unique subset of (3,5,7)")
        if not math.isfinite(self.physical_error_rate) or not 0 < self.physical_error_rate < .5:
            raise ValueError("Uniform circuit probability must lie in (0,.5)")
        for name in ('shots_per_point','batch_size','num_workers'):
            if type(getattr(self,name)) is not int or getattr(self,name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.master_seed) is not int or self.master_seed < 0:
            raise ValueError("master_seed must be a nonnegative integer")

    def resolved(self) -> dict:
        """Return JSON-ready complete settings, with absolute output path."""
        result = asdict(self)
        result['output_root'] = str(self.output_root.resolve())
        return result

    @property
    def config_hash(self) -> str:
        """Return SHA256 of all resolved settings, independent of runtime state."""
        return hashlib.sha256(json.dumps(self.resolved(),sort_keys=True).encode()).hexdigest()


def memory_batch_tasks(config: CircuitLevelMemoryConfig, experiment_id: str) -> Iterator[BatchTask]:
    """Yield the existing immutable BatchTask type with memory-specific seed identity.

    Args: config: Validated memory settings; experiment_id: Run directory name.
    Yields: Deterministic tasks whose identity includes d, rounds, p and noise type.
    """
    for d in config.distances:
        identity = f"memory_uniform_d{d}_t{d}_p{config.physical_error_rate:.12g}"
        for batch, offset in enumerate(range(0,config.shots_per_point,config.batch_size)):
            yield BatchTask(experiment_id,identity,d,config.physical_error_rate,batch,offset,
                min(config.batch_size,config.shots_per_point-offset), batch_seed(config.master_seed,identity,batch))


@lru_cache(maxsize=3)
def memory_code_pair(distance: int, probability: float) -> tuple[ColorCode, ColorCode, CircuitLevelDecoder]:
    """Build/cache ordinary and comparative physical memory plus its swim adapter.

    Args: distance: Odd d=rounds in {3,5,7}; probability: uniform circuit noise rate.
    Returns: (ordinary ColorCode, comparative ColorCode, CircuitLevelDecoder).
    Raises: ValueError: Physical record pairing or static topology gate fails.
    """
    if distance not in (3,5,7):
        raise ValueError("Only the small validation grid is supported")
    options = dict(d=distance, rounds=distance, circuit_type='tri', cnot_schedule='tri_optimal',
                   noise_model=NoiseModel.uniform_circuit_noise(probability))
    ordinary = ColorCode(**options)
    comparative = ColorCode(**options, comparative_decoding=True)
    validate_pairing(ordinary.circuit,comparative.circuit)
    return ordinary,comparative,CircuitLevelDecoder(ordinary)


def sample_memory_batch(task: BatchTask) -> pd.DataFrame:
    """Sample physical circuit once; pair ordinary swim with existing comparative gap.

    Args: task: Deterministic shared BatchTask with rounds=distance.
    Returns: Complete per-shot table; weights/swim/gap use natural-log units.
    Raises: ValueError: Any hard-result, topology, pairing or storage invariant fails.
    Notes: Every shot's ordinary prediction, weight, selected color and correction
        are checked against the replay with growth enabled. No resampling pairs scores.
    """
    code, comparative, decoder = memory_code_pair(task.distance,task.physical_error_rate)
    det, actual = code.sample(task.shots,seed=task.seed)
    pred, extra = decoder.decode(det)
    actual = np.asarray(actual,dtype=bool).ravel()
    cpred, comp = comparative.decode(np.column_stack((det,actual)),full_output=True)
    values = dict(experiment_id=task.experiment_id,config_id=task.config_id,batch_id=task.batch_id,
        shot_index=np.arange(task.offset,task.offset+task.shots),batch_seed=np.full(task.shots,task.seed,dtype=np.uint64),
        distance=task.distance,rounds=task.distance,physical_error_rate=task.physical_error_rate,
        noise_model_name=NOISE_MODEL_NAME,actual_observable=actual,ordinary_prediction=pred,
        ordinary_logical_error=pred != actual,ordinary_selected_color=np.array(list('rgb'))[extra['best_colors']],
        ordinary_solution_weight=extra['weights'],selected_swim_distance=extra['selected_swim_distance'],
        comparative_prediction=np.asarray(cpred,dtype=bool),comparative_logical_error=cpred != actual,
        forced_gap=comp['logical_gaps'],comparative_logical_gap=comp['logical_gaps'],
        swim_bound_certified=False,hard_output_invariant=True)
    for i,c in enumerate('rgb'):
        values[f'stage2_weight_{c}'] = extra['stage2_weights_by_color'][:,i]
        values[f'swim_distance_{c}'] = extra['swim_distances_by_color'][:,i]
        values[f'swim_method_{c}'] = extra['swim_methods_by_color'][i]
        values[f'balance_passed_{c}'] = extra['balance_passed_by_color'][i]
        values[f'class_exists_{c}'] = extra['class_exists_by_color'][i]
    result = pd.DataFrame(values)
    validate_memory_shots(result)
    return result


def comparative_candidate_weights(comparative: ColorCode, detector_outcomes: np.ndarray) -> np.ndarray:
    """Decode all two-logical-class by three-color comparative candidates.

    Args:
        comparative: The paired ``comparative_decoding=True`` color code.
        detector_outcomes: Comparative detector input, including its final forced bit.
    Returns:
        Float array with shape ``(shots, 2, 3)`` in logical-class 0/1 and rgb order.
    Raises:
        ValueError: The code/input is incompatible or a public forced decode is malformed.
    Notes:
        This uses the decoder's public ``logical_value`` and ``colors`` controls.  It
        does not modify the external decoder merely to expose its otherwise discarded
        six-candidate weight tensor.
    """
    values = np.asarray(detector_outcomes, dtype=bool)
    if values.ndim == 1:
        values = values.reshape(1, -1)
    if values.ndim != 2 or values.shape[1] != comparative.circuit.num_detectors:
        raise ValueError("Expected a two-dimensional comparative detector array")
    if not comparative.comparative_decoding or comparative.circuit.num_observables != 1:
        raise ValueError("Expected a one-observable comparative decoder")
    weights = np.empty((len(values), 2, 3), dtype=float)
    for logical_class in (0, 1):
        for color_index, color in enumerate(COMPARATIVE_COLORS):
            prediction, extra = comparative.decode(
                values, colors=color, logical_value=(bool(logical_class),), full_output=True
            )
            forced_prediction = np.asarray(prediction, dtype=bool)
            if forced_prediction.shape != (len(values),) or not np.all(forced_prediction == bool(logical_class)):
                raise ValueError("Forced comparative decode returned the wrong logical class")
            candidate = np.asarray(extra["weights"], dtype=float)
            if candidate.shape != (len(values),) or not np.isfinite(candidate).all():
                raise ValueError("Malformed comparative candidate weights")
            weights[:, logical_class, color_index] = candidate
    return weights


def summarize_comparative_candidates(weights: np.ndarray) -> dict[str, np.ndarray]:
    """Apply the existing comparative argmin convention to a six-weight tensor.

    The baseline is the minimum-weight logical class and the forced correction is
    the other class.  Color ties follow rgb order; a logical-class tie follows 0,1.
    """
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 3 or weights.shape[1:] != (2, 3) or not np.isfinite(weights).all():
        raise ValueError("Candidate weights must have shape (shots, 2, 3) and be finite")
    class_colors = np.argmin(weights, axis=2)
    class_weights = np.min(weights, axis=2)
    baseline_class = np.argmin(class_weights, axis=1)
    forced_class = 1 - baseline_class
    rows = np.arange(len(weights))
    baseline_weight = class_weights[rows, baseline_class]
    forced_weight = class_weights[rows, forced_class]
    return {
        "baseline_logical_class": baseline_class.astype(bool),
        "forced_logical_class": forced_class.astype(bool),
        "baseline_color": np.asarray(COMPARATIVE_COLORS)[class_colors[rows, baseline_class]],
        "forced_color": np.asarray(COMPARATIVE_COLORS)[class_colors[rows, forced_class]],
        "baseline_weight": baseline_weight,
        "forced_weight": forced_weight,
        "forced_gap": forced_weight - baseline_weight,
    }


def sample_comparative_candidate_batch(task: BatchTask) -> pd.DataFrame:
    """Replay one deterministic physical batch and return all six candidate weights.

    This is a sidecar-data worker for completed legacy runs.  The physical sample is
    reproduced from the original task seed; it is not an additional statistical run.
    """
    code, comparative, _ = memory_code_pair(task.distance, task.physical_error_rate)
    detectors, actual = code.sample(task.shots, seed=task.seed)
    comparative_input = np.column_stack((detectors, np.asarray(actual, dtype=bool).ravel()))
    weights = comparative_candidate_weights(comparative, comparative_input)
    selected = summarize_comparative_candidates(weights)
    values = dict(
        config_id=task.config_id,
        batch_id=task.batch_id,
        shot_index=np.arange(task.offset, task.offset + task.shots),
        batch_seed=np.full(task.shots, task.seed, dtype=np.uint64),
        distance=task.distance,
        physical_error_rate=task.physical_error_rate,
        **selected,
    )
    for logical_class in (0, 1):
        for color_index, color in enumerate(COMPARATIVE_COLORS):
            values[f"weight_class_{logical_class}_{color}"] = weights[:, logical_class, color_index]
    result = pd.DataFrame(values)
    validate_comparative_candidate_shots(result)
    return result


COMPARATIVE_CANDIDATE_SCHEMA = pa.schema([
    pa.field("config_id", pa.string(), nullable=False),
    pa.field("batch_id", pa.int32(), nullable=False),
    pa.field("shot_index", pa.int64(), nullable=False),
    pa.field("batch_seed", pa.uint64(), nullable=False),
    pa.field("distance", pa.int16(), nullable=False),
    pa.field("physical_error_rate", pa.float64(), nullable=False),
    pa.field("baseline_logical_class", pa.bool_(), nullable=False),
    pa.field("forced_logical_class", pa.bool_(), nullable=False),
    pa.field("baseline_color", pa.string(), nullable=False),
    pa.field("forced_color", pa.string(), nullable=False),
    pa.field("baseline_weight", pa.float64(), nullable=False),
    pa.field("forced_weight", pa.float64(), nullable=False),
    pa.field("forced_gap", pa.float64(), nullable=False),
    *[pa.field(f"weight_class_{logical_class}_{color}", pa.float64(), nullable=False)
      for logical_class in (0, 1) for color in COMPARATIVE_COLORS],
])


def validate_comparative_candidate_shots(frame: pd.DataFrame) -> None:
    """Validate identities, six weights, argmins, colors and reconstructed gap."""
    names = COMPARATIVE_CANDIDATE_SCHEMA.names
    if frame.empty or not set(names).issubset(frame.columns) or frame[names].isna().any().any():
        raise ValueError("Incomplete comparative candidate table")
    if frame.duplicated(["config_id", "batch_id", "shot_index"]).any():
        raise ValueError("Duplicate comparative candidate shot identity")
    columns = [f"weight_class_{logical_class}_{color}"
               for logical_class in (0, 1) for color in COMPARATIVE_COLORS]
    weights = frame[columns].to_numpy(dtype=float).reshape(len(frame), 2, 3)
    expected = summarize_comparative_candidates(weights)
    for name, value in expected.items():
        if not np.array_equal(frame[name].to_numpy(), value):
            raise ValueError(f"Comparative candidate summary mismatch: {name}")
    if not frame.baseline_color.isin(COMPARATIVE_COLORS).all() or not frame.forced_color.isin(COMPARATIVE_COLORS).all():
        raise ValueError("Unknown comparative candidate color")


CIRCUIT_SHOT_SCHEMA = pa.schema(list(SHOT_SCHEMA) + [
    pa.field('rounds',pa.int16(),nullable=False),pa.field('noise_model_name',pa.string(),nullable=False),
    pa.field('swim_bound_certified',pa.bool_(),nullable=False),pa.field('hard_output_invariant',pa.bool_(),nullable=False),
    *[pa.field(f'{name}_{c}',dtype,nullable=False) for c in 'rgb' for name,dtype in (
        ('swim_method',pa.string()),('balance_passed',pa.bool_()),('class_exists',pa.bool_()))]])


def validate_memory_shots(frame: pd.DataFrame) -> None:
    """Validate shared shot semantics plus the closed-memory experiment contract.

    Args: frame: Nonempty full-schema circuit shot table.
    Returns: None on success.
    Raises: ValueError: Invalid memory dimensions, status, methods or certification.
    """
    validate_shots(frame)
    if not set(CIRCUIT_SHOT_SCHEMA.names).issubset(frame.columns) or frame[CIRCUIT_SHOT_SCHEMA.names].isna().any().any():
        raise ValueError("Missing circuit-level shot fields")
    for field in CIRCUIT_SHOT_SCHEMA:
        if pa.types.is_boolean(field.type) and frame[field.name].dtype != bool:
            raise ValueError(f"Expected boolean field: {field.name}")
    if not (frame['rounds'] == frame.distance).all() or not (frame.noise_model_name == NOISE_MODEL_NAME).all():
        raise ValueError("Expected closed d-round uniform-noise memory")
    if frame.swim_bound_certified.any() or not frame.hard_output_invariant.all():
        raise ValueError("Uncertified growth/hard invariance flags inconsistent")
    for c in 'rgb':
        if not frame[f'class_exists_{c}'].all():
            raise ValueError("Standard measured-sector branch has no opposite class")
        expected = np.where(frame[f'balance_passed_{c}'],'two_boundary','logical_cover')
        if not np.array_equal(frame[f'swim_method_{c}'],expected):
            raise ValueError("Analysis method disagrees with balance gate")
