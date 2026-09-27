"""Shared scalar/sequence selection and descriptive filenames."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class PlotSeries:
    """One selected parameter pair and its varying-parameter legend identity."""
    distance: int
    physical_error_rate: float
    varying_parameter: str
    varying_value: float
    label: str


def select_series(distance, physical_error_rate) -> tuple[list[PlotSeries], str]:
    """Resolve scalar/list or list/scalar selections consistently across plots.

    Args:
        distance: Integer or nonempty sequence of integers.
        physical_error_rate: Float or nonempty sequence of floats.
    Returns:
        Series descriptors and a deterministic parameter filename suffix.
    Raises:
        ValueError: Both arguments are sequences, empty, or contain duplicates.
    """
    d_scalar, p_scalar = np.isscalar(distance), np.isscalar(physical_error_rate)
    if not d_scalar and not p_scalar:
        raise ValueError("Only one of distance and physical_error_rate may be a sequence")
    distances = [distance] if d_scalar else list(distance)
    probabilities = [physical_error_rate] if p_scalar else list(physical_error_rate)
    if not distances or not probabilities or len(set(distances)) != len(distances) or len(set(probabilities)) != len(probabilities):
        raise ValueError("Nonempty unique parameter selections required")
    varying = "physical_error_rate" if not p_scalar else "distance"
    series = [PlotSeries(d, p, varying, p if varying == "physical_error_rate" else d,
                        f"p={p:g}" if varying == "physical_error_rate" else f"d={d}")
              for d in distances for p in probabilities]
    if d_scalar and p_scalar:
        suffix = f"d{distance}_p{physical_error_rate:g}"
    elif p_scalar:
        suffix = f"p{physical_error_rate:g}_vary_d" + "-".join(map(str,distances))
    else:
        suffix = f"d{distance}_vary_p" + "-".join(f"{p:g}" for p in probabilities)
    return series, suffix
