"""Saved-data path-gap analysis with explicit, decoder-specific failure labels."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .dataset import Phase2ADataset, METRIC_FAILURES
from .statistics import wilson_interval, rounded_scores
from ..experiments.path_gap_test import (SHOT_SCHEMA, LEGACY_SHOT_SCHEMA, METRIC_VERSION,
    LEGACY_METRIC_VERSION, PathGapTestConfig, sample_batch, validate_shots)

METRICS = ("ordinary_path_gap", "comparative_path_gap", "forced_gap")


class PathGapDataset(Phase2ADataset):
    """Read named signed path-gap columns, never masquerading as SWIM scores."""
    score_label = r"Final-correction path gap $\phi$"
    metric_display_name = "path gap"
    plot_title = "Final-correction path-gap heuristic"

    def __init__(self, run_directory):
        metadata = json.loads((Path(run_directory) / "metadata.json").read_text())
        self.metric_version = metadata.get("metric_version", LEGACY_METRIC_VERSION)
        if self.metric_version not in (METRIC_VERSION, LEGACY_METRIC_VERSION):
            raise ValueError("Unknown path-gap metric version")
        self.versioned_shots = metadata.get("shot_schema_version") == 2 or self.metric_version == METRIC_VERSION
        schema = SHOT_SCHEMA if self.versioned_shots else LEGACY_SHOT_SCHEMA
        super().__init__(run_directory, shot_schema=schema)
        self.plot_title = f"Final-correction path-gap heuristic ({self.metric_version})"
        if self.metadata.get("experiment_name") != "path_gap_test":
            raise ValueError("Not a path-gap experiment")

    def metric_rows(self, metric, *, failure_column=None, **filters):
        if metric not in METRICS or failure_column not in (None, METRIC_FAILURES.get(metric)):
            raise ValueError("Path-gap metrics require their own decoder failure labels")
        return super().metric_rows(metric, failure_column=failure_column, **filters)


def audit_run(dataset, *, replay=True):
    """Stream all shards; check complete identities, summaries and optional replay.

    Replay checks the first batch of each (d,p), not just one parameter. Source
    drift is reported separately; it prevents claiming exact-code reproduction.
    """
    if replay and not dataset.versioned_shots:
        raise ValueError("Legacy metric replay requires archived v1 source; use replay=False for saved-data audit")
    from functools import partial
    from ._paired_audit import audit_paired_run

    def validator(frame):
        if dataset.versioned_shots and "metric_version" not in frame:
            raise ValueError("Missing shot metric version")
        validate_shots(frame, metric_version=dataset.metric_version)

    return audit_paired_run(dataset, config_class=PathGapTestConfig, validator=validator,
                            worker=partial(sample_batch, metric_version=dataset.metric_version), replay=replay)


def matched_retention(dataset, *, distance, physical_error_rate,
                      fractions=(1., .9, .75, .5), round_digits=None, metrics=METRICS):
    """Compare scores at equal retained counts with outcome-independent tie breaks.

    Threshold plots retain whole ties. This separate table splits boundary ties
    by stable shot identity, never by logical outcome, to match retained counts.
    Intervals are 99% pointwise Wilson, not paired-difference confidence bounds.
    """
    fractions = tuple(fractions)
    if not fractions or any(not np.isfinite(f) or not 0 < f <= 1 for f in fractions):
        raise ValueError("Retained fractions must be finite and in (0,1]")
    distances = [distance] if np.isscalar(distance) else list(distance)
    probabilities = [physical_error_rate] if np.isscalar(physical_error_rate) else list(physical_error_rate)
    records = []
    for d in distances:
        for p in probabilities:
            for metric in metrics:
                rows = dataset.metric_rows(metric, distance=d, physical_error_rate=p)
                if rows.empty:
                    raise ValueError(f"No samples for d={d}, p={p}")
                score = rounded_scores(rows[metric], round_digits)
                order = np.argsort(-score, kind="stable")
                failures = rows[METRIC_FAILURES[metric]].to_numpy()
                cumulative = np.cumsum(failures[order])
                for fraction in fractions:
                    count = max(1, int(fraction*len(rows)))
                    errors = int(cumulative[count-1])
                    low, high = wilson_interval(errors, count)
                    records.append(dict(distance=d, physical_error_rate=p, metric=metric,
                                        failure_column=METRIC_FAILURES[metric], target_retained=fraction,
                                        retained_fraction=count/len(rows), retained_shots=count,
                                        retained_failures=errors, residual_logical_error_rate=errors/count,
                                        low=float(low), high=float(high),
                                        tie_rule="descending score, then config_id/batch_id/shot_index"))
    return pd.DataFrame(records)
