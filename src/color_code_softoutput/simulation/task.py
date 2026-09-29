"""Immutable inputs for the future simulation worker."""

from dataclasses import dataclass


PAIRED_METRICS = ("logical_error", "default_logical_error",
                  "better_weight_by_color_correlated_decoding",
                  "effect_by_color_correlated_decoding")


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
    decoder_alias: str | None = None


def metric_names(point: ResolvedPoint) -> tuple[str, ...]:
    """The per-shot output contract shared by decoder requests and storage."""
    options = dict(point.color_code_options) | dict(point.decoder_options)
    paired = PAIRED_METRICS
    if options.get("enable_colorcorrelated_decoding", False):
        names = (*paired, "color_correlated_run")
    elif options.get("enable_cross_color_relifting", False):
        names = (*paired, "relift_run")
    elif options.get("enable_prior_perturbation", False) or options.get("stage1_perturbation", False):
        names = paired
    else:
        names = ("logical_error",)
    if dict(point.decode_options).get("compute_swim_distance", False):
        names += ("swim_distance",)
    if options.get("comparative_decoding", False):
        names += ("logical_gap",)
    return names
