"""Canonical YAML experiment runner; workers return data to main-process storage."""

from __future__ import annotations

from datetime import datetime
import inspect
import json
import os
from pathlib import Path

from color_code_stim import ColorCode

from .config import WorkflowConfig, load_workflow_config, resolve_native_seeds
from .planner import plan_points, point_directory_name, run_directory_name
from .scheduler import run_scheduler
from .task import ResolvedPoint
from .worker import _construct
from .workflow_storage import PointStorage


def _now() -> datetime:
    return datetime.now().astimezone()


def _preflight_point(point: ResolvedPoint) -> None:
    """Check the native constructor and public decode options before any run exists."""
    if point.decoder_type not in ("concat_mwpm", "concat_mwpm_stage2_base",
                                  "color_correlated", "relifting", "perturbation", "tesseract"):
        raise ValueError(f"unsupported decoder type: {point.decoder_type}")
    correlated = dict(point.color_code_options) | dict(point.decoder_options)
    if (point.decoder_type == "color_correlated") != correlated.get("enable_colorcorrelated_decoding", False):
        raise ValueError(f"decoder type and correlated option disagree: {point.decoder_type}")
    for label, flag in (("relifting", "enable_cross_color_relifting"),
                        ("perturbation", "enable_prior_perturbation")):
        if (point.decoder_type == label) != correlated.get(flag, False):
            raise ValueError(f"decoder type and {flag} option disagree: {point.decoder_type}")
    if point.decoder_type != "tesseract":
        inspect.signature(ColorCode.decode).bind(None, None, **dict(point.decode_options))
    if dict(point.decode_options).get("compute_swim_distance", False):
        if correlated.get("comparative_decoding", False):
            raise ValueError("swim distance and comparative decoding cannot be combined")
    pair = _construct(point)
    if dict(point.decode_options).get("bp_predecoding", False):
        import ldpc
        pair.configured.dem_manager.global_projection
    if correlated.get("stage1_perturbation", False):
        import numpy as np
        # Validate native topology/prior support before creating a run directory.
        if not dict(point.decode_options).get('bp_predecoding', False):
            pair.configured.decode(np.zeros((0, pair.configured.circuit.num_detectors), dtype=bool))
    if dict(point.decode_options).get("compute_swim_distance", False) and not dict(point.decode_options).get('bp_predecoding', False):
        if pair.circuit_swim is None:
            from color_code_stim.soft_output.pymatching_backend import Stage2Backend
            for color in "rgb":
                Stage2Backend(pair.configured.dem_manager, color)


def _write_log(path: Path, record: dict) -> None:
    temporary = path.with_name(".run_log.json.tmp")
    if temporary.exists():
        raise FileExistsError(temporary)
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run_experiment(config: WorkflowConfig | str | Path, *, reporter=print) -> Path:
    """Validate, run a bounded spawn sweep, and return its unique run directory."""
    if not isinstance(config, WorkflowConfig):
        config = load_workflow_config(config)
    config = resolve_native_seeds(config)
    points = plan_points(config)
    for point in points:
        _preflight_point(point)
    started = _now()
    root = config.simulation.output_root.expanduser().resolve() / run_directory_name(config, started)
    root.mkdir(parents=True, exist_ok=False)
    stores: dict[str, PointStorage] = {}
    record = {"config": config.semantic_dict(), "simulation_start_time": started.isoformat(),
              "simulation_end_time": None}
    native_points = [p for p in points if
        (dict(p.color_code_options) | dict(p.decoder_options)).get('stage1_perturbation', False)]
    if native_points:
        schemes = {p.point_id: 2 if dict(p.decode_options).get('bp_predecoding', False) else 1
                   for p in native_points}
        versions = set(schemes.values())
        record["native_stage1_perturbation"] = {
            "scheme_version": next(iter(versions)) if len(versions) == 1 else 'mixed',
            "shot_index": "absolute_per_point", "color_stream_ids": {"r": 0, "g": 1, "b": 2}}
        if 2 in versions:
            record['native_stage1_perturbation']['scheme_version_by_point'] = schemes
    if any(dict(p.decode_options).get("bp_predecoding", False) for p in points):
        from importlib.metadata import version
        from color_code_stim.dem_utils.global_dem import GLOBAL_BP_VERSION, GLOBAL_BP_WEIGHT_RULE
        record["global_bp_predecoding"] = {
            "version": GLOBAL_BP_VERSION, "ldpc_version": version("ldpc"), "probability_cap": .5,
            "weight_rule": GLOBAL_BP_WEIGHT_RULE,
            "aggregation": "independent_xor", "effective_probability": "p/(1+p)",
            "stage1_prior": "bp_posterior", "stage2_prior": "original_physical",
            "selection_prior": "original_physical", "selection_weight_basis": "original_dem",
            "native_perturbation_scheme_version": 2,
            "null_metrics": "concat metrics are null on BP-converged shots"}
    record["config"]["simulation"]["output_root"] = str(config.simulation.output_root.expanduser().resolve())
    log_path = root / "run_log.json"
    try:
        for point in points:
            stores[point.point_id] = PointStorage(point, root / point_directory_name(point),
                                                  config.simulation.buffer_shots)
        _write_log(log_path, record)
        if config.simulation.verbose:
            reporter(f"run directory: {root}; points: {len(points)}; total requested shots: "
                     f"{sum(p.shots for p in points)}; configured workers: {config.simulation.workers}")

        def accept(result) -> None:
            store = stores[result.point_id]
            store.accept(result)
            if store.next_contiguous_shot == store.point.shots:
                store.finalize()

        progress = run_scheduler(config, points, accept, reporter=reporter)
        if any(p.completed_shots != p.total_shots for p in progress):
            raise RuntimeError("scheduler returned before all shots completed")
        if any(not store._finalized for store in stores.values()):
            raise RuntimeError("a point did not finalize")
    finally:
        record["simulation_end_time"] = _now().isoformat()
        _write_log(log_path, record)
    return root
