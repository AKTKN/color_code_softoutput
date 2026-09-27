"""Immutable inputs for the future simulation worker."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedPoint:
    point_id: str
    decoder_type: str
    distance: int
    physical_error_rate: float
    noise_model: str
    rounds: int
    circuit_type: str
    cnot_schedule: str
    shots: int
    color_code_options: tuple[tuple[str, object], ...]
    decoder_options: tuple[tuple[str, object], ...]
    decode_options: tuple[tuple[str, object], ...]

