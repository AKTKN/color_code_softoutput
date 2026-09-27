"""Explicit YAML noise names for the installed color-code-stim API."""

import math

from color_code_stim import NoiseModel


NOISE_NAMES = frozenset({"bitflip", "depol", "uniform"})


def make_noise_model(name: str, p: float) -> NoiseModel:
    """Construct the exact native model named by a validated sweep point."""
    if name not in NOISE_NAMES:
        raise ValueError(f"Unknown noise model: {name!r}")
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("physical_error_rate must be finite and in [0, 1]")
    if name == "bitflip":
        return NoiseModel(bitflip=p)
    if name == "depol":
        return NoiseModel(depol=p)
    return NoiseModel.uniform_circuit_noise(p)
