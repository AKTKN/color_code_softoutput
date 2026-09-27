"""Paired one-round path-gap experiments; no SWIM backend is required.

Load the feature metric separately from the installed decoder environment.
Both subtraction conventions use the public ColorCodePathGap distances and weights.
"""
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache, partial
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import pyarrow as pa

from ..simulation.config import Phase2ATestConfig, PROJECT_ROOT, batch_tasks
from ..simulation.pairing import validate_pairing
from ..simulation.parallel_runner import completed_batches
from ..simulation.provenance import (
    archive_sources, environment_metadata, repository_state, write_json,
)
from ..simulation.storage import write_shard


@dataclass(frozen=True)
class PathGapTestConfig(Phase2ATestConfig):
    """Same grid and infrastructure defaults as phase2a_getting_started.ipynb."""
    batch_size: int = 2_000
    num_workers: int = 6
    master_seed: int = 20260912321


@lru_cache(maxsize=1)
def require_path_gap():
    """Load the public metric without replacing the installed SWIM decoder.

    The feature's metrics/config modules are isolated in a private namespace;
    color_code_stim's imports and search path remain unchanged. No source copy
    or process-wide sys.path modification is performed.
    """
    try:
        from color_code_stim.metrics import ColorCodePathGap
    except ModuleNotFoundError as error:
        if error.name != "color_code_stim.metrics":
            raise
        import importlib
        from importlib.machinery import ModuleSpec
        import sys
        from types import ModuleType
        source = PROJECT_ROOT / "external_libs/color-code-stim-path-gap/src/color_code_stim"
        if not (source / "metrics/__init__.py").is_file():
            raise RuntimeError(f"Missing path-gap feature source: {source}") from error
        name = "_color_code_softoutput_path_gap"
        if name not in sys.modules:
            package = ModuleType(name)
            package.__path__ = [str(source)]
            package.__package__ = name
            package.__spec__ = ModuleSpec(name, loader=None, is_package=True)
            package.__spec__.submodule_search_locations = package.__path__
            sys.modules[name] = package
        ColorCodePathGap = importlib.import_module(f"{name}.metrics").ColorCodePathGap
    return ColorCodePathGap


METRIC_VERSION = "path_overlap_v2"
LEGACY_METRIC_VERSION = "global_subtraction_v1"


def normalize_metric_version(metric_version):
    """Accept v1/v2 or their canonical provenance names; reject unknown modes."""
    versions = {"v1": LEGACY_METRIC_VERSION, "v2": METRIC_VERSION,
                LEGACY_METRIC_VERSION: LEGACY_METRIC_VERSION, METRIC_VERSION: METRIC_VERSION}
    if not isinstance(metric_version, str) or metric_version not in versions:
        raise ValueError("Unknown path-gap metric version; choose v1 or v2")
    return versions[metric_version]


_TYPES = {
    "experiment_id": pa.string(), "config_id": pa.string(),
    "batch_id": pa.int32(), "shot_index": pa.int64(), "batch_seed": pa.uint64(),
    "distance": pa.int16(), "physical_error_rate": pa.float64(),
    "actual_observable": pa.bool_(), "forced_gap": pa.float64(),
}
for _decoder in ("ordinary", "comparative"):
    _TYPES.update({f"{_decoder}_{name}": dtype for name, dtype in {
        "prediction": pa.bool_(), "logical_error": pa.bool_(),
        "selected_color": pa.string(), "solution_weight": pa.float64(),
        "path_gap": pa.float64(), "correction_weight": pa.float64(),
        "minimizing_color": pa.string(),
        **{f"{prefix}_{c}": pa.float64() for prefix in ("distance", "phi") for c in "rgb"},
    }.items()})
LEGACY_SHOT_SCHEMA = pa.schema([pa.field(k, v, nullable=False) for k, v in _TYPES.items()])
_TYPES["metric_version"] = pa.string()
_TYPES.update({f"{decoder}_overlap_{c}": pa.float64()
               for decoder in ("ordinary", "comparative") for c in "rgb"})
SHOT_SCHEMA = pa.schema([pa.field(k, v, nullable=False) for k, v in _TYPES.items()])


def validate_shots(frame, *, metric_version=None):
    """Validate versioned v1/v2 shots or unversioned legacy v1 data."""
    versioned = "metric_version" in frame
    if frame.empty:
        raise ValueError("Complete nonempty nonnull path-gap shot schema required")
    version = normalize_metric_version(metric_version if metric_version is not None else
                                      (frame.metric_version.iloc[0] if versioned else LEGACY_METRIC_VERSION))
    types = _TYPES if versioned else {f.name: f.type for f in LEGACY_SHOT_SCHEMA}
    if (versioned and not frame.metric_version.eq(version).all()) or (not versioned and version == METRIC_VERSION):
        raise ValueError("Inconsistent path-gap metric version")
    if not set(types).issubset(frame) or frame[list(types)].isna().any().any():
        raise ValueError("Complete nonempty nonnull path-gap shot schema required")
    if frame.duplicated(["config_id", "batch_id", "shot_index"]).any():
        raise ValueError("Duplicate shot identity")
    for name, dtype in types.items():
        if pa.types.is_floating(dtype) and not np.isfinite(frame[name]).all():
            raise ValueError(f"Nonfinite {name}")
        if pa.types.is_boolean(dtype) and frame[name].dtype != bool:
            raise ValueError(f"Nonboolean {name}")
    if not frame.distance.isin(range(3, 16, 2)).all() or not frame.physical_error_rate.between(0, .5, inclusive="neither").all():
        raise ValueError("Unsupported physical parameters")
    if (frame.forced_gap < 0).any():
        raise ValueError("Negative comparative forced gap")
    for decoder in ("ordinary", "comparative"):
        distances = frame[[f"{decoder}_distance_{c}" for c in "rgb"]].to_numpy()
        phi = frame[[f"{decoder}_phi_{c}" for c in "rgb"]].to_numpy()
        weight = frame[f"{decoder}_correction_weight"].to_numpy()
        if (distances < 0).any() or (weight < 0).any():
            raise ValueError("Negative physical weights or residual distances")
        if versioned:
            overlap = frame[[f"{decoder}_overlap_{c}" for c in "rgb"]].to_numpy()
            if (overlap < 0).any() or (overlap > weight[:, None] + 1e-12).any():
                raise ValueError("Invalid path overlap weight")
        subtraction = overlap if version == METRIC_VERSION else weight[:, None]
        if not np.allclose(phi, distances-subtraction, rtol=1e-12, atol=1e-12):
            raise ValueError("Incorrect correction-weight subtraction")
        if not np.array_equal(phi.min(axis=1), frame[f"{decoder}_path_gap"]):
            raise ValueError("Incorrect minimum across colors")
        if not np.array_equal(np.array(list("rgb"))[phi.argmin(axis=1)], frame[f"{decoder}_minimizing_color"]):
            raise ValueError("Incorrect minimizing color")
        if not frame[f"{decoder}_selected_color"].isin(list("rgb")).all():
            raise ValueError("Invalid hard-decoder color")
        if not np.array_equal(frame[f"{decoder}_prediction"] != frame.actual_observable,
                              frame[f"{decoder}_logical_error"]):
            raise ValueError("Incorrect decoder failure association")


@lru_cache(maxsize=2)
def _models(distance, probability):
    metric_class = require_path_gap()
    from color_code_stim import ColorCode, NoiseModel
    options = dict(d=distance, rounds=1, circuit_type="tri", cnot_schedule="tri_optimal",
                   noise_model=NoiseModel(bitflip=probability))
    ordinary = ColorCode(**options)
    comparative = ColorCode(**options, comparative_decoding=True)
    validate_pairing(ordinary.circuit, comparative.circuit)
    return ordinary, comparative, metric_class(ordinary), metric_class(comparative)


def sample_batch(task, *, metric_version=METRIC_VERSION):
    """Sample paired shots using v1 (total correction) or v2 (path overlap).

    Both modes use the same public residual distances, weights and hard outputs.
    The default remains v2 for compatibility with existing callers.
    """
    metric_version = normalize_metric_version(metric_version)
    started = perf_counter()
    ordinary, comparative, metric, comparative_metric = _models(task.distance, task.physical_error_rate)
    setup_seconds = perf_counter() - started
    detectors, actual = ordinary.sample(task.shots, seed=task.seed)
    actual = np.asarray(actual, dtype=bool).reshape(-1)
    record = dict(metric_version=metric_version, experiment_id=task.experiment_id, config_id=task.config_id,
                  batch_id=task.batch_id, shot_index=np.arange(task.offset, task.offset+task.shots),
                  batch_seed=np.full(task.shots, task.seed, dtype=np.uint64),
                  distance=task.distance, physical_error_rate=task.physical_error_rate,
                  actual_observable=actual)
    timings = dict(setup_seconds=setup_seconds)
    # Forced decoding overwrites the extra detector. Never pass the truth label.
    forced_input = np.column_stack((detectors, np.zeros(task.shots, dtype=bool)))
    for name, code, evaluator, inputs in (
        ("ordinary", ordinary, metric, detectors),
        ("comparative", comparative, comparative_metric, forced_input),
    ):
        before = perf_counter()
        prediction, extra = code.decode(inputs, full_output=True)
        timings[f"{name}_decode_seconds"] = perf_counter()-before
        frozen = {key: value.copy() for key, value in extra.items() if isinstance(value, np.ndarray)}
        before = perf_counter()
        result = evaluator.evaluate(extra)
        if result.metric_version != METRIC_VERSION:
            raise ValueError("Path-gap metric source version mismatch")
        # V1 subtracts the entire final correction from each residual distance.
        # The public v2 evaluator retains both inputs; no graph/search changes.
        phi_by_color = (result.distance_by_color - result.correction_weight[:, None]
                        if metric_version == LEGACY_METRIC_VERSION else result.phi_by_color)
        minimizing = phi_by_color.argmin(axis=1)
        phi = phi_by_color[np.arange(task.shots), minimizing]
        minimizing_color = np.asarray(result.color_order)[minimizing]
        timings[f"{name}_metric_seconds"] = perf_counter()-before
        for key, value in frozen.items():
            np.testing.assert_array_equal(extra[key], value)
        # Audit hard-decision invariance on a bounded prefix after evaluation.
        again, check = code.decode(inputs[:min(16, task.shots)], full_output=True)
        np.testing.assert_array_equal(again, prediction[:len(again)])
        for key in ("weights", "best_colors"):
            np.testing.assert_array_equal(check[key], extra[key][:len(again)])
        prediction = np.asarray(prediction, dtype=bool).reshape(-1)
        for key, value in dict(prediction=prediction, logical_error=prediction != actual,
                               selected_color=np.array(list("rgb"))[extra["best_colors"]],
                               solution_weight=extra["weights"], path_gap=phi,
                               correction_weight=result.correction_weight,
                               minimizing_color=minimizing_color).items():
            record[f"{name}_{key}"] = value
        for index, color in enumerate(result.color_order):
            record[f"{name}_distance_{color}"] = result.distance_by_color[:, index]
            record[f"{name}_phi_{color}"] = phi_by_color[:, index]
            record[f"{name}_overlap_{color}"] = result.overlap_weight_by_color[:, index]
        if name == "comparative":
            record["forced_gap"] = extra["logical_gaps"]
    frame = pd.DataFrame(record)
    validate_shots(frame)
    frame.attrs["timings"] = timings
    return frame


def run_experiment(config=None, *, metric_version=METRIC_VERSION):
    """Write bounded-memory, deterministic Parquet batches and source provenance.

    Returns the new run directory. Failed runs retain atomic completed shards;
    automatic resumption is deliberately unsupported. Full defaults: 6M shots.
    metric_version: "v1" / "global_subtraction_v1" subtracts total W(E);
        "v2" / "path_overlap_v2" (default) subtracts per-color path overlap.
    """
    config = config or PathGapTestConfig()
    metric_version = normalize_metric_version(metric_version)
    require_path_gap()
    import color_code_stim
    import pymatching
    started = perf_counter()
    timestamp = datetime.now().astimezone()
    experiment_id = timestamp.strftime("%Y%m%d_%H%M%S_%f_path_gap_test")
    directory = config.output_root / experiment_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "shots").mkdir()
    (directory / "figures").mkdir()
    environment = environment_metadata()
    checkout = Path(color_code_stim.__file__).resolve().parents[2]
    import inspect
    metric_source = Path(inspect.getfile(require_path_gap())).resolve()
    metric_checkout = metric_source.parents[3]
    environment["imported_package_paths"]["path_gap_metric"] = str(metric_source)
    environment["repositories"]["path-gap-feature"] = repository_state(metric_checkout)
    environment["repositories"]["original_SWIM_color-code-stim"] = environment["repositories"]["color-code-stim"]
    environment["repositories"]["color-code-stim"] = repository_state(checkout)
    environment["repositories"]["original_SWIM_PyMatching"] = environment["repositories"]["PyMatching"]
    matching_checkout = Path(pymatching.__file__).resolve().parents[2]
    environment["repositories"]["PyMatching"] = dict(**repository_state(matching_checkout), version=pymatching.__version__, path=pymatching.__file__)
    for root in {checkout, metric_checkout}:
        for path in (root / "src").rglob("*.py"):
            environment["source_hashes"][str(path.relative_to(PROJECT_ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata = dict(**environment, experiment_id=experiment_id, experiment_name="path_gap_test",
                    timestamp=timestamp.isoformat(), resolved_config=config.resolved(),
                    config_hash=config.config_hash, status="running", confidence_level=.99,
                    metric_version=metric_version, shot_schema_version=2,
                    metric_description=("Signed final-correction heuristic phi=min_c [D_c(E)-"
                                        + ("W(E)" if metric_version == LEGACY_METRIC_VERSION else "W(E intersect L_c)")
                                        + "]; not SWIM, an exact logical gap, or a calibrated LLR."),
                    metric_failure_labels={"ordinary_path_gap":"ordinary_logical_error",
                                           "comparative_path_gap":"comparative_logical_error",
                                           "forced_gap":"comparative_logical_error"},
                    pairing="Same physical shot; audited detector prefix; forced extra input is zero, not ground truth.",
                    rounds=1, cnot_schedule="tri_optimal", noise_model="NoiseModel(bitflip=p)",
                    seed_recipe="Same batch_tasks/SeedSequence recipe as phase2a_test; exact replay also requires same batch size and environment.",
                    limitations="Finite Monte Carlo, 99% pointwise Wilson intervals; no posterior or threshold theorem.")
    write_json(directory / "metadata.json", metadata)
    archive_sources(directory / "source_snapshot.zip", metadata["source_hashes"])
    write_json(directory / "resolved_config.json", config.resolved())
    counts, timings = {}, []
    completed = 0
    total = len(config.distances)*len(config.probabilities)*config.shots_per_point
    try:
        worker = partial(sample_batch, metric_version=metric_version)
        for task, frame in completed_batches(batch_tasks(config, experiment_id), num_workers=config.num_workers, worker=worker):
            write_shard(frame, directory / "shots" / f"{task.config_id}_batch{task.batch_id:06d}.parquet",
                        config.config_hash, schema=SHOT_SCHEMA,
                        validator=partial(validate_shots, metric_version=metric_version))
            row = counts.setdefault(task.config_id, dict(config_id=task.config_id, distance=task.distance,
                                    physical_error_rate=task.physical_error_rate, shots=0,
                                    ordinary_failures=0, comparative_failures=0))
            row["shots"] += task.shots
            for name in ("ordinary", "comparative"):
                row[f"{name}_failures"] += int(frame[f"{name}_logical_error"].sum())
            timings.append(dict(config_id=task.config_id, batch_id=task.batch_id, **frame.attrs["timings"]))
            completed += task.shots
            if config.verbose:
                print(f"path-gap: {completed}/{total} shots; {perf_counter()-started:.1f}s", flush=True)
        pd.DataFrame(counts.values()).sort_values("config_id").to_parquet(directory / "summary.parquet", index=False)
        pd.DataFrame(timings).to_parquet(directory / "timings.parquet", index=False)
        metadata["status"] = "sampling_complete"
    except BaseException as error:
        metadata.update(status="failed", error=repr(error))
        raise
    finally:
        metadata.update(completed_shots=completed, completed_batches=len(timings), elapsed_seconds=perf_counter()-started)
        write_json(directory / "metadata.json", metadata)
    return directory


def main():
    """CLI: --smoke preserves the full grid but uses 128 shots per point."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--shots", type=int, default=100_000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=20260912321)
    parser.add_argument("--metric-version", choices=("v1", "v2", LEGACY_METRIC_VERSION, METRIC_VERSION),
                        default="v2", help="v1: subtract total correction weight; v2: subtract path overlap (default)")
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "results")
    args = parser.parse_args()
    config = PathGapTestConfig(shots_per_point=128 if args.smoke else args.shots,
                              num_workers=args.workers, batch_size=args.batch_size,
                              master_seed=args.seed, output_root=args.output_root)
    print(run_experiment(config, metric_version=args.metric_version))


if __name__ == "__main__":
    main()
