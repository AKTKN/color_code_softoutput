"""One-chunk, same-shot worker for the staged YAML simulation workflow.

The cache is process-local. A scheduler may submit ``run_chunk`` through a
spawn-based executor; this module creates no processes and writes no files.
"""

from collections import OrderedDict
from dataclasses import dataclass
from time import perf_counter

import numpy as np
from color_code_stim import ColorCode

from .noise import make_noise_model
from .task import ResolvedPoint


CACHE_MAXSIZE = 4


@dataclass(frozen=True)
class WorkerInput:
    point_id: str
    chunk_id: int
    shot_start: int
    shot_count: int
    seed: int
    point: ResolvedPoint

    def __post_init__(self) -> None:
        if self.point_id != self.point.point_id:
            raise ValueError("point_id does not match resolved point")
        for name in ("chunk_id", "shot_start", "seed"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if type(self.shot_count) is not int or self.shot_count <= 0:
            raise ValueError("shot_count must be a positive integer")
        if self.shot_start + self.shot_count > self.point.shots:
            raise ValueError("chunk exceeds resolved point shot count")


@dataclass(frozen=True)
class WorkerResult:
    point_id: str
    chunk_id: int
    shot_start: int
    shot_count: int
    elapsed_seconds: float
    metrics: dict[str, np.ndarray]


@dataclass
class _CodePair:
    configured: ColorCode
    ordinary: ColorCode | None
    tesseract_decoder: object | None = None
    circuit_swim: object | None = None


_CODE_CACHE: OrderedDict[tuple, _CodePair] = OrderedDict()


def _semantics(point: ResolvedPoint) -> tuple:
    return (point.distance, point.physical_error_rate, point.noise_model,
            point.rounds, point.circuit_type, point.cnot_schedule,
            point.color_code_options, point.decoder_options, point.decoder_type)


def _construct(point: ResolvedPoint) -> _CodePair:
    is_tesseract = point.decoder_type == "tesseract"
    options = dict(point.color_code_options)
    if not is_tesseract:
        options.update(point.decoder_options)
    options.update(d=point.distance, rounds=point.rounds,
                   circuit_type=point.circuit_type,
                   cnot_schedule=point.cnot_schedule,
                   noise_model=make_noise_model(point.noise_model, point.physical_error_rate))
    configured = ColorCode(**options)
    if is_tesseract:
        if configured.temp_bdry_type not in ("X", "Z"):
            raise ValueError("tesseract XYZ decoding is not supported; select X or Z temporal boundary")
        if configured.dem_xz.num_detectors != configured.circuit.num_detectors:
            raise ValueError("original X/Z DEM detector order does not match sampled circuit")
    ordinary = None
    if options.get("enable_colorcorrelated_decoding", False):
        ordinary = ColorCode(**(options | {"enable_colorcorrelated_decoding": False}))
        # Stim circuit equality checks instructions, detector annotations and
        # observable annotations, including their ordering.
        if ordinary.circuit != configured.circuit:
            raise ValueError("ordinary and correlated circuits differ")
    if is_tesseract:
        from .tesseract import compile_tesseract
        return _CodePair(configured, None, compile_tesseract(configured.dem_xz, point.decoder_options))
    circuit_swim = None
    if dict(point.decode_options).get("compute_swim_distance", False) and not configured.dem_manager.swim_data_only:
        from .circuit_swim import CircuitCandidateSwim
        circuit_swim = CircuitCandidateSwim(configured)
    return _CodePair(configured, ordinary, circuit_swim=circuit_swim)


def _codes(point: ResolvedPoint) -> _CodePair:
    key = _semantics(point)
    if key in _CODE_CACHE:
        _CODE_CACHE.move_to_end(key)
        return _CODE_CACHE[key]
    pair = _construct(point)
    _CODE_CACHE[key] = pair
    if len(_CODE_CACHE) > CACHE_MAXSIZE:
        _CODE_CACHE.popitem(last=False)
    return pair


def logical_errors(prediction: np.ndarray, actual: np.ndarray, shots: int) -> np.ndarray:
    """Return one failure bit per shot, reducing over multiple observables."""
    pred = np.asarray(prediction, dtype=bool)
    obs = np.asarray(actual, dtype=bool)
    if pred.shape != obs.shape or pred.ndim not in (1, 2) or pred.shape[0] != shots:
        raise ValueError("prediction and actual observables must align by shot")
    if pred.ndim == 2 and pred.shape[1] < 1:
        raise ValueError("at least one observable is required")
    return (np.any(pred != obs, axis=-1) if pred.ndim == 2 else pred != obs).astype(bool)


def better_common_prior_weight(extra: dict, shots: int) -> np.ndarray:
    """Strict improvement over the ordinary three candidates in common prior.

    The first three candidates are the ordinary r/g/b matchings. All
    candidate_weights use the selected common basis: unchanged color stage-2
    priors or unchanged original X/Z DEM priors. Temporary generation weights
    are deliberately ignored.
    """
    weights = np.asarray(extra["candidate_weights"], dtype=float)
    if (weights.ndim != 3 or weights.shape[1] < 3 or weights.shape[2] != shots
            or not np.isfinite(weights[:, :3, :]).all()
            or np.isnan(weights).any() or np.isneginf(weights).any()):
        raise ValueError("expected finite ordinary weights and finite/+inf candidate weights shaped (classes, candidates>=3, shots)")
    ordinary = np.min(weights[:, :3, :], axis=(0, 1))
    selected = np.asarray(extra["weights"], dtype=float)
    if selected.shape != (shots,) or not np.isfinite(selected).all():
        raise ValueError("expected one finite selected weight per shot")
    # Recompute the selected minimum from the public candidate tensor so both
    # sides have the same reduction convention. Exact < preserves true ties.
    best = np.min(weights, axis=(0, 1))
    if not np.allclose(selected, best, rtol=1e-12, atol=1e-12):
        raise ValueError("selected weight disagrees with common-prior candidates")
    return (best < ordinary).astype(np.uint8)


def run_chunk(task: WorkerInput) -> WorkerResult:
    """Sample once, decode the same detectors, and return bounded chunk arrays."""
    started = perf_counter()
    pair = _codes(task.point)
    detectors, actual = pair.configured.sample(task.shot_count, seed=task.seed)
    if task.point.decoder_type == "tesseract":
        from .tesseract import decode_tesseract
        predicted = decode_tesseract(pair.tesseract_decoder, detectors,
                                     pair.configured.dem_xz.num_observables)
        actual_array = np.asarray(actual, dtype=bool)
        if actual_array.ndim == 1 and predicted.shape[1] == 1:
            predicted = predicted[:, 0]
        metrics = {"logical_error": logical_errors(predicted, actual_array, task.shot_count)}
        return WorkerResult(task.point_id, task.chunk_id, task.shot_start, task.shot_count,
                            perf_counter() - started, metrics)
    decode_options = dict(task.point.decode_options)
    correlated = pair.ordinary is not None
    options = dict(task.point.color_code_options) | dict(task.point.decoder_options)
    relifting = options.get("enable_cross_color_relifting", False)
    perturbation = options.get("enable_prior_perturbation", False)
    swim = decode_options.get("compute_swim_distance", False)
    comparative = options.get("comparative_decoding", False)
    circuit_swim = swim and pair.circuit_swim is not None
    if circuit_swim:
        decode_options["compute_swim_distance"] = False
        decode_options["return_candidate_data"] = True
    if correlated or relifting or perturbation or swim or comparative:
        # The common-prior comparison requires the public full-output fields.
        decode_options["full_output"] = True
    configured_result = pair.configured.decode(detectors, **decode_options)
    if decode_options.get("full_output", False):
        prediction, extra = configured_result
    else:
        prediction, extra = configured_result, None
    final_fail = logical_errors(prediction, actual, task.shot_count)
    metrics = {"logical_error": final_fail}
    if swim:
        distance = np.asarray(
            pair.circuit_swim.score(detectors, prediction, extra) if circuit_swim
            else extra["class_min_swim_distance"], dtype=np.float64)
        if distance.shape != (task.shot_count,) or not np.isfinite(distance).all() or np.any(distance < 0):
            raise ValueError("invalid selected swim distance")
        metrics["swim_distance"] = distance
    if comparative:
        gap = np.asarray(extra["logical_gaps"], dtype=np.float64)
        if gap.shape != (task.shot_count,) or not np.isfinite(gap).all() or np.any(gap < 0):
            raise ValueError("invalid comparative logical gap")
        metrics["logical_gap"] = gap
    if relifting:
        run_category = np.asarray(extra["relift_run_class"])
        if (run_category.shape != (task.shot_count,)
                or not np.issubdtype(run_category.dtype, np.integer)
                or np.any((run_category < 0) | (run_category > 2))):
            raise ValueError("relift_run must contain 0, 1, or 2 per shot")
        metrics["relift_run"] = run_category.astype(np.uint8)
    if correlated or relifting or perturbation:
        if correlated:
            baseline_options = decode_options | {"full_output": False,
                                                 "return_candidate_data": False}
            default_pred = pair.ordinary.decode(detectors, **baseline_options)
        else:
            default_pred = extra["baseline_predictions"]
        default_fail = logical_errors(default_pred, actual, task.shot_count)
        metrics.update(
            default_logical_error=default_fail,
            better_weight_by_color_correlated_decoding=better_common_prior_weight(extra, task.shot_count),
            effect_by_color_correlated_decoding=(default_fail & ~final_fail).astype(np.uint8),
        )
        if correlated:
            run_category = np.asarray(extra["color_correlated_run"])
            if (run_category.shape != (task.shot_count,)
                    or not np.issubdtype(run_category.dtype, np.integer)
                    or np.any(run_category > 2) or np.any(run_category < 0)):
                raise ValueError("color_correlated_run must contain 0, 1, or 2 per shot")
            metrics["color_correlated_run"] = run_category.astype(np.uint8)
    return WorkerResult(task.point_id, task.chunk_id, task.shot_start, task.shot_count,
                        perf_counter() - started, metrics)
