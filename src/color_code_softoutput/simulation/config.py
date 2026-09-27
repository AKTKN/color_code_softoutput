"""Fixed one-round experiment grid and deterministic batch identities."""
from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DISTANCES = (5, 7, 9, 11, 13, 15)
NEAR_THRESHOLD_PS = (0.082, 0.084, 0.085, 0.086, 0.087, 0.088)
SUBTHRESHOLD_PS = (0.02, 0.03, 0.04, 0.05)
GRID_PROVENANCE = {
    "status": "project approximation: explicit prompt fallback",
    "original_near_threshold_grid": None,
    "original_subthreshold_grid": None,
    "inspection": "Lee Sec. 3.1/Fig. 3; current and historical 53b60e9 getting_started.ipynb; exact original grid not recovered",
    "paper": "https://quantum-journal.org/papers/q-2025-01-27-1609/",
}
FORCED_GAP_SOURCE = "existing color-code-stim comparative-decoding logical gap"
HISTORICAL_NOTE = ("The paper's ~8.2% crossing used historical double bit-flip injection. "
                   "The corrected repository documents ~8.6% and roughly halved LER. "
                   "This study uses corrected code, T=1, and targets coarse agreement.")


@dataclass(frozen=True)
class Phase2ATestConfig:
    """Configure the fixed corrected-code experiment, with counts in shots.

    Args:
        distances: Unique odd distances from 3 through 15; independent of the default grid.
        near_threshold_ps: Probabilities used for LOWESS crossing analysis.
        subthreshold_ps: Probabilities used for log-linear scaling analysis.
        shots_per_point: Positive fixed count per deduplicated (d,p).
        batch_size: Maximum shots returned by a worker at once.
        num_workers: CPU process count; pending work is bounded to twice this.
        master_seed: Nonnegative seed for the NumPy SeedSequence recipe.
        output_root: Parent directory of timestamped runs.
        verbose: Emit batch-completion progress via logging.

    Raises:
        ValueError: Invalid, duplicated, or unsupported parameters.
    """
    distances: tuple[int, ...] = DISTANCES
    near_threshold_ps: tuple[float, ...] = NEAR_THRESHOLD_PS
    subthreshold_ps: tuple[float, ...] = SUBTHRESHOLD_PS
    shots_per_point: int = 100_000
    batch_size: int = 5_000
    num_workers: int = 4
    master_seed: int = 20260912
    output_root: Path = PROJECT_ROOT / "results"
    verbose: bool = True

    def __post_init__(self):
        for name in ("distances", "near_threshold_ps", "subthreshold_ps"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "output_root", Path(self.output_root))
        if not self.distances or any(type(d) is not int or d not in range(3, 16, 2) for d in self.distances):
            raise ValueError("Distances must be odd integers from 3 through 15")
        for values in (self.distances, self.near_threshold_ps, self.subthreshold_ps):
            if len(set(values)) != len(values):
                raise ValueError("Duplicate grid entries")
        if not self.probabilities or any(not math.isfinite(p) or not 0 < p < .5 for p in self.probabilities):
            raise ValueError("Physical probabilities must be finite and in (0,0.5)")
        for name in ("shots_per_point", "batch_size", "num_workers"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.master_seed) is not int or self.master_seed < 0:
            raise ValueError("master_seed must be a nonnegative integer")

    @property
    def probabilities(self) -> tuple[float, ...]:
        """Return sorted, deduplicated physical probabilities across both sweeps."""
        return tuple(sorted(set(self.near_threshold_ps + self.subthreshold_ps)))

    def resolved(self) -> dict:
        """Return a JSON-compatible complete configuration with absolute output path."""
        result = asdict(self)
        result["output_root"] = str(self.output_root.resolve())
        return result

    @property
    def config_hash(self) -> str:
        """Return SHA256 of all resolved configuration values, including infrastructure."""
        return hashlib.sha256(json.dumps(self.resolved(), sort_keys=True).encode()).hexdigest()


def config_id(distance: int, physical_error_rate: float) -> str:
    """Return a deterministic parameter identity independent of scheduling order."""
    return f"d{distance}_p{physical_error_rate:.12g}"


def batch_seed(master_seed: int, configuration_id: str, batch_id: int) -> int:
    """Derive a uint64 Stim seed from SHA256(config ID) and SeedSequence.

    Args:
        master_seed: Nonnegative integer.
        configuration_id: Stable ASCII parameter identity.
        batch_id: Nonnegative batch index within that configuration.
    Returns:
        Python integer representable as an unsigned 64-bit seed.
    """
    digest = hashlib.sha256(configuration_id.encode()).digest()
    words = np.frombuffer(digest, dtype="<u4").tolist()
    return int(np.random.SeedSequence([master_seed, *words, batch_id]).generate_state(1, dtype=np.uint64)[0])


@dataclass(frozen=True)
class BatchTask:
    """Immutable worker input; shot_index starts at offset within a configuration."""
    experiment_id: str
    config_id: str
    distance: int
    physical_error_rate: float
    batch_id: int
    offset: int
    shots: int
    seed: int


def batch_tasks(config: Phase2ATestConfig, experiment_id: str):
    """Yield deterministic bounded-size tasks; no shot arrays are allocated."""
    for distance in config.distances:
        for probability in config.probabilities:
            identity = config_id(distance, probability)
            for batch_id, offset in enumerate(range(0, config.shots_per_point, config.batch_size)):
                yield BatchTask(experiment_id, identity, distance, probability, batch_id, offset,
                                min(config.batch_size, config.shots_per_point-offset),
                                batch_seed(config.master_seed, identity, batch_id))


# The YAML workflow is independent of the historical fixed-grid config above.
_SWEEP_KEYS = frozenset({"distance", "physical_error_rate", "noise_model", "rounds", "circuit_type", "cnot_schedule"})
_CONSTRUCTOR_KEYS = frozenset({"temp_bdry_type", "superdense_circuit", "perfect_logical_initialization",
    "perfect_logical_measurement", "perfect_first_syndrome_extraction", "perfect_init_final",
    "remove_non_edge_like_errors", "comparative_decoding", "enable_colorcorrelated_decoding",
    "color_correlated_weight_basis",
    "exclude_non_essential_pauli_detectors"})
_DECODE_KEYS = frozenset({"colors", "compute_swim_distance", "full_output", "check_validity", "verbose"})
_BOOLEAN_OPTIONS = (_CONSTRUCTOR_KEYS - {"temp_bdry_type", "color_correlated_weight_basis"}) | (_DECODE_KEYS - {"colors"})
_SWEEP_ALIASES = frozenset({"d", "rounds", "circuit_type", "cnot_schedule", "noise_model",
    "p_bitflip", "p_depol", "p_reset", "p_meas", "p_cnot", "p_idle", "p_circuit"})


def _mapping(value, name, *, allowed=None, required=()):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    if allowed is not None and (extra := set(value) - set(allowed)):
        raise ValueError(f"Unknown {name} keys: {sorted(extra)}")
    if missing := set(required) - set(value):
        raise ValueError(f"Missing {name} keys: {sorted(missing)}")
    return value


def _positive_int(value, name, *, zero=False):
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError(f"{name} must be {'nonnegative' if zero else 'positive'} integer")
    return value


def _positive_number(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return float(value)


def _axis(value, name, validate):
    values = value if isinstance(value, list) else [value]
    if not values:
        raise ValueError(f"{name} must not be empty")
    return tuple(validate(v) for v in values)


def _probability(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("physical_error_rate must be finite and in [0, 1]")
    return float(value)


def _distance(value):
    if type(value) is not int or value < 3 or value % 2 != 1:
        raise ValueError("distance must be an odd integer >= 3")
    return value


def _string(value, name):
    if (not isinstance(value, str) or not value or value != value.strip()
            or any(c in value for c in '/\\,=') or any(ord(c) < 32 for c in value)):
        raise ValueError(f"{name} must be a nonempty filesystem-safe string")
    return value


def _freeze(value, name):
    """Keep arbitrary option values JSON-compatible and immutable."""
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, list):
        return tuple(_freeze(v, name) for v in value)
    raise ValueError(f"{name} must contain only finite JSON scalar/list values")


def _options(value, name, allowed):
    value = _mapping(value, name)
    if bad := set(value) & _SWEEP_ALIASES:
        raise ValueError(f"{name} conflicts with sweep: {sorted(bad)}")
    if bad := set(value) - allowed:
        raise ValueError(f"Unsupported {name} keys: {sorted(bad)}")
    for key in set(value) & _BOOLEAN_OPTIONS:
        if type(value[key]) is not bool:
            raise ValueError(f"{name}.{key} must be boolean")
    if "temp_bdry_type" in value and value["temp_bdry_type"] not in (None, "X", "Y", "Z", "x", "y", "z"):
        raise ValueError(f"{name}.temp_bdry_type must be X, Y, Z or null")
    if ("color_correlated_weight_basis" in value
            and value["color_correlated_weight_basis"] not in ("stage2", "original_dem")):
        raise ValueError(f"{name}.color_correlated_weight_basis must be stage2 or original_dem")
    if "colors" in value:
        colors = value["colors"]
        if colors != "all" and colors not in ("r", "g", "b") and not (
            isinstance(colors, list) and bool(colors) and all(c in ("r", "g", "b") for c in colors)
            and len(set(colors)) == len(colors)
        ):
            raise ValueError(f"{name}.colors must be 'all', a color, or a unique color list")
    return tuple((k, _freeze(v, name)) for k, v in sorted(value.items()))


@dataclass(frozen=True)
class SimulationSettings:
    output_root: Path
    shots: int
    workers: int
    master_seed: int
    buffer_shots: int
    verbose: bool


@dataclass(frozen=True)
class ChunkingSettings:
    calibration_shots: int
    target_chunk_seconds: float
    min_chunk_shots: int
    max_chunk_shots: int
    throughput_ema_alpha: float


@dataclass(frozen=True)
class SweepSettings:
    distance: tuple[int, ...]
    physical_error_rate: tuple[float, ...]
    noise_model: tuple[str, ...]
    rounds: tuple[int, ...] | str
    circuit_type: tuple[str, ...]
    cnot_schedule: tuple[str, ...]


@dataclass(frozen=True)
class DecoderSettings:
    type: str
    options: tuple[tuple[str, object], ...]
    decode_options: tuple[tuple[str, object], ...]


@dataclass(frozen=True)
class WorkflowConfig:
    simulation: SimulationSettings
    chunking: ChunkingSettings
    sweep: SweepSettings
    color_code_options: tuple[tuple[str, object], ...]
    decoders: tuple[DecoderSettings, ...]

    def semantic_dict(self) -> dict:
        """Return validated values for hashing, retaining relative output_root.

        Relative roots participate because they are an intentional destination
        choice. Absolute roots are excluded: machine-specific locations must
        not change an otherwise equivalent run hash.
        """
        sim = asdict(self.simulation)
        root = self.simulation.output_root
        sim["output_root"] = root.as_posix() if not root.is_absolute() else None
        return {"simulation": sim, "chunking": asdict(self.chunking), "sweep": asdict(self.sweep),
                "color_code_options": dict(self.color_code_options),
                "decoders": [{"type": d.type, "options": dict(d.options),
                              "decode_options": dict(d.decode_options)} for d in self.decoders]}

    @property
    def hash8(self) -> str:
        encoded = json.dumps(self.semantic_dict(), sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:8]


def parse_workflow_config(data: dict) -> WorkflowConfig:
    """Validate and resolve a YAML mapping without touching output paths."""
    data = _mapping(data, "config", allowed={"simulation", "chunking", "sweep", "color_code_options", "decoders"},
                    required={"simulation", "chunking", "sweep", "decoders"})
    sim = _mapping(data["simulation"], "simulation", allowed={"output_root", "shots", "workers", "master_seed", "buffer_shots", "verbose"},
                   required={"output_root", "shots", "workers", "master_seed", "buffer_shots", "verbose"})
    if not isinstance(sim["output_root"], str) or not sim["output_root"].strip():
        raise ValueError("simulation.output_root must be a nonempty path")
    if type(sim["verbose"]) is not bool:
        raise ValueError("simulation.verbose must be boolean")
    simulation = SimulationSettings(Path(sim["output_root"]), _positive_int(sim["shots"], "shots"),
        _positive_int(sim["workers"], "workers"), _positive_int(sim["master_seed"], "master_seed", zero=True),
        _positive_int(sim["buffer_shots"], "buffer_shots"), sim["verbose"])
    chunk = _mapping(data["chunking"], "chunking", allowed={"calibration_shots", "target_chunk_seconds", "min_chunk_shots", "max_chunk_shots", "throughput_ema_alpha"},
                     required={"calibration_shots", "target_chunk_seconds", "min_chunk_shots", "max_chunk_shots", "throughput_ema_alpha"})
    chunking = ChunkingSettings(_positive_int(chunk["calibration_shots"], "calibration_shots"),
        _positive_number(chunk["target_chunk_seconds"], "target_chunk_seconds"),
        _positive_int(chunk["min_chunk_shots"], "min_chunk_shots"),
        _positive_int(chunk["max_chunk_shots"], "max_chunk_shots"),
        _positive_number(chunk["throughput_ema_alpha"], "throughput_ema_alpha"))
    if chunking.min_chunk_shots > chunking.max_chunk_shots or chunking.throughput_ema_alpha > 1:
        raise ValueError("Invalid chunk size bounds or EMA alpha")
    sweep = _mapping(data["sweep"], "sweep", allowed=_SWEEP_KEYS, required=_SWEEP_KEYS)
    rounds = sweep["rounds"]
    if rounds != "distance":
        rounds = _axis(rounds, "rounds", lambda v: _positive_int(v, "rounds"))
    noise_names = _axis(sweep["noise_model"], "noise_model", lambda v: _string(v, "noise_model"))
    from .noise import NOISE_NAMES
    if unknown := set(noise_names) - NOISE_NAMES:
        raise ValueError(f"Unknown noise model: {sorted(unknown)}")
    sweep_settings = SweepSettings(_axis(sweep["distance"], "distance", _distance),
        _axis(sweep["physical_error_rate"], "physical_error_rate", _probability), noise_names, rounds,
        _axis(sweep["circuit_type"], "circuit_type", lambda v: _string(v, "circuit_type")),
        _axis(sweep["cnot_schedule"], "cnot_schedule", lambda v: _string(v, "cnot_schedule")))
    common = _options(data.get("color_code_options", {}), "color_code_options", _CONSTRUCTOR_KEYS)
    raw_decoders = data["decoders"]
    if not isinstance(raw_decoders, list) or not raw_decoders:
        raise ValueError("decoders must be a nonempty list")
    decoders = []
    for raw in raw_decoders:
        raw = _mapping(raw, "decoder", allowed={"type", "options", "decode_options"}, required={"type"})
        label = _string(raw["type"], "decoder.type")
        options = _options(raw.get("options", {}), "decoder.options", _CONSTRUCTOR_KEYS)
        decode_options = _options(raw.get("decode_options", {}), "decoder.decode_options", _DECODE_KEYS)
        if overlap := set(dict(common)) & set(dict(options)):
            raise ValueError(f"Ambiguous constructor options in color_code_options and decoder.options: {sorted(overlap)}")
        merged = dict(common) | dict(options)
        if merged.get("enable_colorcorrelated_decoding", False) and dict(decode_options).get("compute_swim_distance", False):
            raise ValueError("Color-correlated decoding cannot compute matching-growth SWIM")
        decoders.append(DecoderSettings(label, options, decode_options))
    return WorkflowConfig(simulation, chunking, sweep_settings, common, tuple(decoders))


def load_workflow_config(path: str | Path) -> WorkflowConfig:
    """Read a YAML file and return a validated immutable configuration."""
    with Path(path).open(encoding="utf-8") as stream:
        return parse_workflow_config(yaml.safe_load(stream))
