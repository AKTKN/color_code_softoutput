"""Saved-shot monotone-Y analysis with explicit decoder-specific failure labels."""

from .dataset import Phase2ADataset
from ._paired_audit import audit_paired_run
from .path_gap import matched_retention as _matched_retention
from .path_gap_comparison import compare_postselection as _compare_postselection
from ..experiments.monotone_y_test import (
    METRIC_VERSION,
    METRIC_FAILURE_LABELS,
    SHOT_SCHEMA,
    MonotoneYTestConfig,
    sample_batch,
    validate_shots,
)

METRICS = tuple(METRIC_FAILURE_LABELS)


class MonotoneYDataset(Phase2ADataset):
    """Signed scores on final physical corrections; no per-color aggregation."""

    score_label = r"Monotone-Y signed gap $S_Y$"
    conditional_ler_label = r"$P(\mathrm{logical\ error}\mid S_Y)$"
    metric_display_name = "monotone-Y gap"
    plot_title = "Final-correction monotone-Y signed gap"

    def __init__(self, run_directory):
        super().__init__(run_directory, shot_schema=SHOT_SCHEMA)
        if self.metadata.get("experiment_name") != "monotone_y_test":
            raise ValueError("Not a monotone-Y experiment")
        if (
            self.metadata.get("metric_version") != METRIC_VERSION
            or self.metadata.get("shot_schema_version") != 1
        ):
            raise ValueError("Unknown monotone-Y metric or shot schema version")
        if self.metadata.get("metric_failure_labels") != METRIC_FAILURE_LABELS:
            raise ValueError("Invalid monotone-Y decoder failure labels")
        self.metric_version = METRIC_VERSION

    def metric_rows(self, metric, *, failure_column=None, **filters):
        if metric not in METRICS or failure_column not in (
            None,
            METRIC_FAILURE_LABELS.get(metric),
        ):
            raise ValueError(
                "Monotone-Y metrics require their own decoder failure labels"
            )
        return super().metric_rows(metric, failure_column=failure_column, **filters)


def audit_run(dataset, *, replay=True):
    """Audit every shard and optionally replay the first batch of each (d,p)."""
    return audit_paired_run(
        dataset,
        config_class=MonotoneYTestConfig,
        validator=validate_shots,
        worker=sample_batch,
        replay=replay,
    )


def matched_retention(
    dataset,
    *,
    distance,
    physical_error_rate,
    fractions=(1.0, 0.9, 0.75, 0.5),
    round_digits=None
):
    """Compare the three scores at equal retained counts using stable shot-ID ties."""
    return _matched_retention(
        dataset,
        distance=distance,
        physical_error_rate=physical_error_rate,
        fractions=fractions,
        round_digits=round_digits,
        metrics=METRICS,
    )


def compare_postselection(
    dataset,
    *,
    distance,
    physical_error_rate,
    abort_rates=(0.0, 0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5),
    competitive_margin=1.25,
    round_digits=None,
    output_directory=None
):
    """Save matched-abort and whole-tie tables with each decoder's own failures."""
    return _compare_postselection(
        dataset,
        distance=distance,
        physical_error_rate=physical_error_rate,
        abort_rates=abort_rates,
        competitive_margin=competitive_margin,
        round_digits=round_digits,
        output_directory=output_directory
        or dataset.run_directory / "monotone_y_comparison",
        metrics=METRICS,
        metric_display_name="Monotone-Y",
    )
