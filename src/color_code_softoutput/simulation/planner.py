"""Pure sweep expansion, stable identities, and path collision preflight."""

from datetime import datetime
import hashlib
from itertools import product
import json

from .config import WorkflowConfig, canonical_native_options
from .task import ResolvedPoint


def point_directory_name(point: ResolvedPoint) -> str:
    """Return the exact per-point directory component."""
    alias = f"decoder_alias={point.decoder_alias}," if point.decoder_alias is not None else ""
    return (alias + f"decoder_type={point.decoder_type},circuit_type={point.circuit_type},"
            f"d={point.distance},r={point.rounds},p={format(point.physical_error_rate, '.12g')},"
            f"noisemodel={point.noise_model},cnot_schedule={point.cnot_schedule}")


def run_directory_name(config: WorkflowConfig, timestamp: datetime) -> str:
    """Format a supplied timestamp; the caller chooses its timezone."""
    return f"{timestamp:%y_%m_%d_%H_%M_%S}_{config.hash8}"


def plan_points(config: WorkflowConfig) -> tuple[ResolvedPoint, ...]:
    """Expand and preflight every point before any simulation starts."""
    sweep = config.sweep
    common, decoders = canonical_native_options(config.color_code_options, config.decoders)
    rounds_axis = (None,) if sweep.rounds == "distance" else sweep.rounds
    points = []
    seen_names = set()
    seen_ids = set()
    for d, p, noise, rounds, circuit, schedule, decoder in product(
            sweep.distance, sweep.physical_error_rate, sweep.noise_model, rounds_axis,
            sweep.circuit_type, sweep.cnot_schedule, decoders):
        r = d if rounds is None else rounds
        semantic = {"distance": d, "physical_error_rate": p, "noise_model": noise,
                    "rounds": r, "circuit_type": circuit, "cnot_schedule": schedule,
                    "decoder_type": decoder.type, "color_code_options": dict(common),
                    "decoder_options": dict(decoder.options), "decode_options": dict(decoder.decode_options)}
        if decoder.decoder_alias is not None:
            semantic["decoder_alias"] = decoder.decoder_alias
        digest = hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":"),
                                         allow_nan=False).encode("utf-8")).hexdigest()
        point = ResolvedPoint(digest, decoder.type, d, p, noise, r, circuit, schedule,
                              config.simulation.shots, common,
                              decoder.options, decoder.decode_options, decoder.decoder_alias)
        name = point_directory_name(point)
        if name in seen_names or point.point_id in seen_ids:
            raise ValueError(f"Expanded point path collision: {name}")
        seen_names.add(name)
        seen_ids.add(point.point_id)
        points.append(point)
    return tuple(points)
