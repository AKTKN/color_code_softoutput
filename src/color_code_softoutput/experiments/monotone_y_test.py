"""Paired one-round monotone-Y signed-gap experiments in color_code_so.

The isolated feature metric reads only each decoder's final physical correction.
Sampling, parallel scheduling, storage and source snapshots use shared infrastructure.
"""

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
import hashlib
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import pyarrow as pa

from ..simulation.config import Phase2ATestConfig, PROJECT_ROOT, batch_tasks
from ..simulation.pairing import validate_pairing
from ..simulation.parallel_runner import completed_batches
from ..simulation.provenance import (
    archive_sources,
    environment_metadata,
    repository_state,
    write_json,
)
from ..simulation.storage import write_shard


@dataclass(frozen=True)
class MonotoneYTestConfig(Phase2ATestConfig):
    """Same grid and infrastructure defaults as phase2a_getting_started.ipynb."""

    batch_size: int = 2_000
    num_workers: int = 6
    master_seed: int = 20260912321


@lru_cache(maxsize=1)
def require_monotone_y():
    """Load the feature adapter without changing installed decoder imports.

    The private package loads metrics/config only, from the feature worktree.
    It never modifies sys.path or the installed color_code_stim namespace.
    """
    import importlib
    from importlib.machinery import ModuleSpec
    import sys
    from types import ModuleType

    source = (
        PROJECT_ROOT / "external_libs/color-code-stim-monotone-y/src/color_code_stim"
    )
    if not (source / "metrics/__init__.py").is_file():
        raise RuntimeError(f"Missing monotone-Y feature source: {source}")
    name = "_color_code_softoutput_monotone_y"
    if name not in sys.modules:
        package = ModuleType(name)
        package.__path__ = [str(source)]
        package.__package__ = name
        package.__spec__ = ModuleSpec(name, loader=None, is_package=True)
        package.__spec__.submodule_search_locations = package.__path__
        sys.modules[name] = package
    return importlib.import_module(f"{name}.metrics").MonotoneYGapAdapter


METRIC_VERSION = "monotone_y_signed_v1"
METRIC_FAILURE_LABELS = {
    "ordinary_monotone_y_gap": "ordinary_logical_error",
    "comparative_monotone_y_gap": "comparative_logical_error",
    "forced_gap": "comparative_logical_error",
}
_TYPES = {
    "experiment_id": pa.string(),
    "config_id": pa.string(),
    "batch_id": pa.int32(),
    "shot_index": pa.int64(),
    "batch_seed": pa.uint64(),
    "distance": pa.int16(),
    "physical_error_rate": pa.float64(),
    "actual_observable": pa.bool_(),
    "forced_gap": pa.float64(),
    "metric_version": pa.string(),
}
for _decoder in ("ordinary", "comparative"):
    _TYPES.update(
        {
            f"{_decoder}_{name}": dtype
            for name, dtype in {
                "prediction": pa.bool_(),
                "logical_error": pa.bool_(),
                "selected_color": pa.string(),
                "solution_weight": pa.float64(),
                "monotone_y_gap": pa.float64(),
                "correction_weight": pa.float64(),
                "root_id": pa.int32(),
                "template_id": pa.int32(),
            }.items()
        }
    )
SHOT_SCHEMA = pa.schema([pa.field(k, v, nullable=False) for k, v in _TYPES.items()])


def validate_shots(frame):
    """Validate finite signed scores, physical bounds and hard failure labels.

    Numerical bounds are necessary checks, not a proof of the saved minimum.
    Deterministic replay checks that minimum and its root/template diagnostics.
    """
    if (
        frame.empty
        or not set(_TYPES).issubset(frame)
        or frame[list(_TYPES)].isna().any().any()
    ):
        raise ValueError("Complete nonempty nonnull monotone-Y shot schema required")
    if not frame.metric_version.eq(METRIC_VERSION).all():
        raise ValueError("Unknown monotone-Y metric version")
    if frame.duplicated(["config_id", "batch_id", "shot_index"]).any():
        raise ValueError("Duplicate shot identity")
    for name, dtype in _TYPES.items():
        if pa.types.is_floating(dtype) and not np.isfinite(frame[name]).all():
            raise ValueError(f"Nonfinite {name}")
        if pa.types.is_boolean(dtype) and frame[name].dtype != bool:
            raise ValueError(f"Nonboolean {name}")
        if pa.types.is_integer(dtype) and (
            not pd.api.types.is_integer_dtype(frame[name]) or (frame[name] < 0).any()
        ):
            raise ValueError(f"Invalid integer {name}")
    if (
        not frame.distance.isin(range(3, 16, 2)).all()
        or not frame.physical_error_rate.between(0, 0.5, inclusive="neither").all()
    ):
        raise ValueError("Unsupported physical parameters")
    if (frame.forced_gap < 0).any():
        raise ValueError("Negative comparative forced gap")
    n = (3 * frame.distance.to_numpy(dtype=np.int64) ** 2 + 1) // 4
    p = frame.physical_error_rate.to_numpy()
    unit = np.log1p(-p) - np.log(p)
    for decoder in ("ordinary", "comparative"):
        score = frame[f"{decoder}_monotone_y_gap"].to_numpy()
        weight = frame[f"{decoder}_correction_weight"].to_numpy()
        # Every candidate is a physical binary support: -W(E) <= S <= W(all)-W(E).
        if (
            (weight < 0).any()
            or (weight > n * unit + 1e-10).any()
            or (score < -weight - 1e-10).any()
            or (score > n * unit - weight + 1e-10).any()
        ):
            raise ValueError("Invalid signed physical weight bounds")
        if (frame[f"{decoder}_root_id"] >= n).any():
            raise ValueError("Invalid physical root ID")
        if not frame[f"{decoder}_selected_color"].isin(list("rgb")).all():
            raise ValueError("Invalid hard-decoder color")
        if not np.array_equal(
            frame[f"{decoder}_prediction"] != frame.actual_observable,
            frame[f"{decoder}_logical_error"],
        ):
            raise ValueError("Incorrect decoder failure association")


@lru_cache(maxsize=2)
def _models(distance, probability):
    metric_class = require_monotone_y()
    from color_code_stim import ColorCode, NoiseModel

    options = dict(
        d=distance,
        rounds=1,
        circuit_type="tri",
        cnot_schedule="tri_optimal",
        noise_model=NoiseModel(bitflip=probability),
    )
    ordinary = ColorCode(**options)
    comparative = ColorCode(**options, comparative_decoding=True)
    validate_pairing(ordinary.circuit, comparative.circuit)
    return ordinary, comparative, metric_class(ordinary), metric_class(comparative)


def sample_batch(task):
    """Score final corrections on the same physical shots with unchanged decoding."""
    started = perf_counter()
    ordinary, comparative, metric, comparative_metric = _models(
        task.distance, task.physical_error_rate
    )
    setup_seconds = perf_counter() - started
    detectors, actual = ordinary.sample(task.shots, seed=task.seed)
    actual = np.asarray(actual, dtype=bool).reshape(-1)
    record = dict(
        metric_version=METRIC_VERSION,
        experiment_id=task.experiment_id,
        config_id=task.config_id,
        batch_id=task.batch_id,
        shot_index=np.arange(task.offset, task.offset + task.shots),
        batch_seed=np.full(task.shots, task.seed, dtype=np.uint64),
        distance=task.distance,
        physical_error_rate=task.physical_error_rate,
        actual_observable=actual,
    )
    timings = dict(setup_seconds=setup_seconds)
    # Forced decoding overwrites the extra detector. Never pass the truth label.
    forced_input = np.column_stack((detectors, np.zeros(task.shots, dtype=bool)))
    for name, code, evaluator, inputs in (
        ("ordinary", ordinary, metric, detectors),
        ("comparative", comparative, comparative_metric, forced_input),
    ):
        before = perf_counter()
        prediction, extra = code.decode(inputs, full_output=True)
        timings[f"{name}_decode_seconds"] = perf_counter() - before
        frozen = {
            key: value.copy()
            for key, value in extra.items()
            if isinstance(value, np.ndarray)
        }
        before = perf_counter()
        result = evaluator.evaluate_decode_output(extra)
        if result.metric_version != METRIC_VERSION:
            raise ValueError("Monotone-Y metric source version mismatch")
        timings[f"{name}_metric_seconds"] = perf_counter() - before
        for key, value in frozen.items():
            np.testing.assert_array_equal(extra[key], value)
        # Audit hard-decision invariance on a bounded prefix after evaluation.
        again, check = code.decode(inputs[: min(16, task.shots)], full_output=True)
        np.testing.assert_array_equal(again, prediction[: len(again)])
        for key in ("weights", "best_colors", "error_preds"):
            np.testing.assert_array_equal(check[key], extra[key][: len(again)])
        prediction = np.asarray(prediction, dtype=bool).reshape(-1)
        for key, value in dict(
            prediction=prediction,
            logical_error=prediction != actual,
            selected_color=np.array(list("rgb"))[extra["best_colors"]],
            solution_weight=extra["weights"],
            monotone_y_gap=result.signed_gap,
            correction_weight=result.correction_weight,
            root_id=result.root_id,
            template_id=result.template_id,
        ).items():
            record[f"{name}_{key}"] = value
        if name == "comparative":
            record["forced_gap"] = extra["logical_gaps"]
    frame = pd.DataFrame(record)
    validate_shots(frame)
    frame.attrs["timings"] = timings
    return frame


def run_experiment(config=None):
    """Write deterministic paired Parquet batches and exact source provenance.

    Full API defaults: 6M shots. The CLI --smoke uses 128 shots per point.
    Failed runs retain completed shards; directories are never reused.
    """
    config = config or MonotoneYTestConfig()
    require_monotone_y()
    import color_code_stim
    import pymatching

    started = perf_counter()
    timestamp = datetime.now().astimezone()
    experiment_id = timestamp.strftime("%Y%m%d_%H%M%S_%f_monotone_y_test")
    directory = config.output_root / experiment_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "shots").mkdir()
    (directory / "figures").mkdir()
    environment = environment_metadata()
    checkout = Path(color_code_stim.__file__).resolve().parents[2]
    import inspect

    metric_source = Path(inspect.getfile(require_monotone_y())).resolve()
    metric_checkout = metric_source.parents[3]
    environment["imported_package_paths"]["monotone_y_metric"] = str(metric_source)
    environment["repositories"]["monotone-y-feature"] = repository_state(
        metric_checkout
    )
    environment["repositories"]["original_SWIM_color-code-stim"] = environment[
        "repositories"
    ]["color-code-stim"]
    environment["repositories"]["color-code-stim"] = repository_state(checkout)
    environment["repositories"]["original_SWIM_PyMatching"] = environment[
        "repositories"
    ]["PyMatching"]
    matching_checkout = Path(pymatching.__file__).resolve().parents[2]
    environment["repositories"]["PyMatching"] = dict(
        **repository_state(matching_checkout),
        version=pymatching.__version__,
        path=pymatching.__file__,
    )
    for root in {checkout, metric_checkout}:
        for path in (root / "src").rglob("*.py"):
            environment["source_hashes"][str(path.relative_to(PROJECT_ROOT))] = (
                hashlib.sha256(path.read_bytes()).hexdigest()
            )
    metadata = dict(
        **environment,
        experiment_id=experiment_id,
        experiment_name="monotone_y_test",
        timestamp=timestamp.isoformat(),
        resolved_config=config.resolved(),
        config_hash=config.config_hash,
        status="running",
        confidence_level=0.99,
        metric_version=METRIC_VERSION,
        shot_schema_version=1,
        metric_description="Signed restricted logical minimum S_Y(E)=min_Y [W(E xor L)-W(E)]; upper bound on the correction-relative unrestricted minimum, not an exact logical gap or calibrated LLR.",
        metric_failure_labels=METRIC_FAILURE_LABELS,
        metric_geometry="Canonical physical columns; certified monotone-tail separation; root/template IDs index the archived geometry construction, not decoder colors.",
        metric_weights="Uniform physical log((1-p)/p), from the one-layer independent-X DEM.",
        pairing="Same physical shot; audited detector prefix; forced extra input is zero, not ground truth.",
        rounds=1,
        cnot_schedule="tri_optimal",
        noise_model="NoiseModel(bitflip=p)",
        seed_recipe="Same batch_tasks/SeedSequence recipe as phase2a_test; exact replay also requires same batch size and environment.",
        limitations="Finite Monte Carlo, 99% pointwise Wilson intervals; no posterior or threshold theorem.",
    )
    write_json(directory / "metadata.json", metadata)
    archive_sources(directory / "source_snapshot.zip", metadata["source_hashes"])
    write_json(directory / "resolved_config.json", config.resolved())
    counts, timings = {}, []
    completed = 0
    total = len(config.distances) * len(config.probabilities) * config.shots_per_point
    try:
        worker = sample_batch
        for task, frame in completed_batches(
            batch_tasks(config, experiment_id),
            num_workers=config.num_workers,
            worker=worker,
        ):
            write_shard(
                frame,
                directory
                / "shots"
                / f"{task.config_id}_batch{task.batch_id:06d}.parquet",
                config.config_hash,
                schema=SHOT_SCHEMA,
                validator=validate_shots,
            )
            row = counts.setdefault(
                task.config_id,
                dict(
                    config_id=task.config_id,
                    distance=task.distance,
                    physical_error_rate=task.physical_error_rate,
                    shots=0,
                    ordinary_failures=0,
                    comparative_failures=0,
                ),
            )
            row["shots"] += task.shots
            for name in ("ordinary", "comparative"):
                row[f"{name}_failures"] += int(frame[f"{name}_logical_error"].sum())
            timings.append(
                dict(
                    config_id=task.config_id,
                    batch_id=task.batch_id,
                    **frame.attrs["timings"],
                )
            )
            completed += task.shots
            if config.verbose:
                print(
                    f"monotone-Y: {completed}/{total} shots; {perf_counter()-started:.1f}s",
                    flush=True,
                )
        pd.DataFrame(counts.values()).sort_values("config_id").to_parquet(
            directory / "summary.parquet", index=False
        )
        pd.DataFrame(timings).to_parquet(directory / "timings.parquet", index=False)
        metadata["status"] = "sampling_complete"
    except BaseException as error:
        metadata.update(status="failed", error=repr(error))
        raise
    finally:
        metadata.update(
            completed_shots=completed,
            completed_batches=len(timings),
            elapsed_seconds=perf_counter() - started,
        )
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
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "results")
    args = parser.parse_args()
    config = MonotoneYTestConfig(
        shots_per_point=128 if args.smoke else args.shots,
        num_workers=args.workers,
        batch_size=args.batch_size,
        master_seed=args.seed,
        output_root=args.output_root,
    )
    print(run_experiment(config))


if __name__ == "__main__":
    main()
