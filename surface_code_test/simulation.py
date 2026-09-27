"""Deterministic paired surface-memory sampling and strict shot storage."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from collections.abc import Iterator
import numpy as np
import pandas as pd
import pyarrow as pa
from color_code_softoutput.simulation.config import batch_seed
from .model import ROOT, model, PATH_GAP_VERSION

NOISE_MODEL = 'PyMatching.SO_example.Meta_Circuit(circuit_level_depolarizing)'


@dataclass(frozen=True)
class SurfaceConfig:
    """Small closed X-memory grid with the SO_example noise and round convention.

    Args:
        distances: Distinct odd distances >=3.
        physical_error_rate: Common example circuit noise parameter, default .001.
        rounds_factor: SE_round calls per distance; default 2 matches the example.
        shots_per_point, batch_size, num_workers: Positive sampling settings.
        master_seed: Nonnegative deterministic seed; batching changes the sample.
        output_root: Destination for new timestamped runs; no resume/overwrite.
    Raises: ValueError for invalid settings. No windows or herald discards supported.
    """
    distances: tuple[int,...] = (3,5,7)
    physical_error_rate: float = .001
    rounds_factor: int = 2
    shots_per_point: int = 2000
    batch_size: int = 250
    num_workers: int = 3
    master_seed: int = 20260916
    output_root: Path = ROOT/'surface_code_test/results'

    def __post_init__(self):
        object.__setattr__(self,'distances',tuple(self.distances))
        object.__setattr__(self,'output_root',Path(self.output_root))
        if not self.distances or len(set(self.distances)) != len(self.distances) or any(type(d) is not int or d<3 or d%2!=1 for d in self.distances):
            raise ValueError('Distinct odd distances >=3 required')
        if not np.isfinite(self.physical_error_rate) or not 0 < self.physical_error_rate < .5:
            raise ValueError('Noise probability must lie in (0,.5)')
        for name in ('rounds_factor','shots_per_point','batch_size','num_workers'):
            if type(getattr(self,name)) is not int or getattr(self,name) < 1:
                raise ValueError(f'{name} must be a positive integer')
        if type(self.master_seed) is not int or self.master_seed < 0:
            raise ValueError('Nonnegative master_seed required')

    def resolved(self) -> dict:
        """Return JSON-compatible complete settings with absolute output root."""
        values = asdict(self)
        values['output_root'] = str(self.output_root.resolve())
        return values

    @property
    def config_hash(self) -> str:
        """SHA256 identity of all run settings, including worker and batch settings."""
        return hashlib.sha256(json.dumps(self.resolved(),sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class SurfaceTask:
    """One deterministic physical batch; offset indexes shots within a grid point."""
    experiment_id: str
    config_id: str
    distance: int
    rounds: int
    physical_error_rate: float
    batch_id: int
    offset: int
    shots: int
    seed: int


def batch_tasks(config: SurfaceConfig, experiment_id: str) -> Iterator[SurfaceTask]:
    """Yield reproducible tasks in distance/batch order; schedule does not affect seeds."""
    for d in config.distances:
        rounds = config.rounds_factor*d
        cid = f'surface_x_d{d}_r{rounds}_p{config.physical_error_rate:.17g}'
        for i,offset in enumerate(range(0,config.shots_per_point,config.batch_size)):
            yield SurfaceTask(experiment_id,cid,d,rounds,config.physical_error_rate,i,offset,
                min(config.batch_size,config.shots_per_point-offset),batch_seed(config.master_seed,cid,i))


LEGACY_SHOT_SCHEMA = pa.schema([pa.field(name,kind,nullable=False) for name,kind in {
    'experiment_id':pa.string(),'config_id':pa.string(),'batch_id':pa.int32(),
    'shot_index':pa.int64(),'batch_seed':pa.uint64(),'distance':pa.int32(),'rounds':pa.int32(),
    'physical_error_rate':pa.float64(),'noise_model_name':pa.string(),
    'actual_observable':pa.bool_(),'ordinary_prediction':pa.bool_(),'ordinary_logical_error':pa.bool_(),
    'ordinary_solution_weight':pa.float64(),'swim_distance':pa.float64(),
    'complementary_gap':pa.float64(),'class_weight_0':pa.float64(),'class_weight_1':pa.float64(),
    'swim_bound_certified':pa.bool_(),
}.items()])


SHOT_SCHEMA = pa.schema(list(LEGACY_SHOT_SCHEMA) + [
    pa.field('path_gap',pa.float64(),nullable=False),
    pa.field('path_gap_residual_distance',pa.float64(),nullable=False),
    pa.field('path_gap_correction_weight',pa.float64(),nullable=False),
    pa.field('path_gap_metric_version',pa.string(),nullable=False),
])


def validate_shots(frame: pd.DataFrame) -> None:
    """Reject invalid schema, identities, scores or paired prediction/gap semantics.

    Args: frame: Nonempty unprojected shot table, natural-log costs.
    Raises: ValueError/AssertionError for any failed semantic invariant.
    """
    schema = LEGACY_SHOT_SCHEMA if set(frame.columns) == set(LEGACY_SHOT_SCHEMA.names) else SHOT_SCHEMA
    if frame.empty or set(frame.columns) != set(schema.names) or frame.isna().any().any():
        raise ValueError('Complete nonempty surface shot schema required')
    if frame.duplicated(['config_id','batch_id','shot_index']).any():
        raise ValueError('Duplicate shot identity')
    for field in schema:
        if pa.types.is_floating(field.type) and (not np.isfinite(frame[field.name]).all() or (field.name != 'path_gap' and (frame[field.name]<0).any())):
            raise ValueError(f'Invalid finite nonnegative field: {field.name}')
        if pa.types.is_boolean(field.type) and frame[field.name].dtype != bool:
            raise ValueError(f'Expected boolean {field.name}')
    if frame.swim_bound_certified.any() or not (frame.noise_model_name == NOISE_MODEL).all():
        raise ValueError('Unexpected certification or noise model')
    if not np.array_equal(frame.ordinary_logical_error, frame.ordinary_prediction != frame.actual_observable):
        raise ValueError('Incorrect ordinary failure labels')
    weights = frame[['class_weight_0','class_weight_1']].to_numpy()
    np.testing.assert_array_equal(frame.complementary_gap,np.abs(weights[:,1]-weights[:,0]))
    np.testing.assert_allclose(frame.ordinary_solution_weight,weights.min(axis=1),atol=1e-8,rtol=1e-10)
    np.testing.assert_allclose(frame.ordinary_solution_weight,weights[np.arange(len(frame)),frame.ordinary_prediction.astype(int)],atol=1e-8,rtol=1e-10)

    if schema is SHOT_SCHEMA:
        if not (frame.path_gap_metric_version == PATH_GAP_VERSION).all():
            raise ValueError('Unknown path-gap metric version')
        np.testing.assert_array_equal(frame.path_gap,
            frame.path_gap_residual_distance-frame.path_gap_correction_weight)


def sample_batch(task: SurfaceTask) -> pd.DataFrame:
    """Sample once and evaluate swim, complementary gap and path gap on the same shots.

    Args: task: Immutable deterministic batch descriptor.
    Returns: Validated per-shot DataFrame; no rounding, discards or score binning.
    Raises: Any decoder/hard invariance or schema failure propagates.
    """
    decoder = model(task.distance,task.rounds,task.physical_error_rate)
    det, actual = decoder.circuit.compile_detector_sampler(seed=task.seed).sample(task.shots,separate_observables=True)
    result = decoder.decode(det)
    frame = pd.DataFrame(dict(experiment_id=task.experiment_id,config_id=task.config_id,
        batch_id=task.batch_id,shot_index=np.arange(task.offset,task.offset+task.shots),
        batch_seed=np.full(task.shots,task.seed,dtype=np.uint64),distance=task.distance,rounds=task.rounds,
        physical_error_rate=task.physical_error_rate,noise_model_name=NOISE_MODEL,
        actual_observable=actual[:,0],ordinary_prediction=result.prediction,
        ordinary_logical_error=result.prediction != actual[:,0],ordinary_solution_weight=result.solution_weight,
        swim_distance=result.swim_distance,complementary_gap=result.complementary_gap,
        path_gap=result.path_gap,path_gap_residual_distance=result.path_gap_residual_distance,
        path_gap_correction_weight=result.path_gap_correction_weight,path_gap_metric_version=PATH_GAP_VERSION,
        class_weight_0=result.class_weights[:,0],class_weight_1=result.class_weights[:,1],swim_bound_certified=False))
    validate_shots(frame)
    return frame
