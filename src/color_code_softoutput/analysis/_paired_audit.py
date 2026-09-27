"""Streamed integrity/replay audit shared by final-correction experiments."""

import hashlib
import numpy as np
import pandas as pd
from ..simulation.config import batch_tasks, PROJECT_ROOT
from ..simulation.provenance import write_json


def audit_paired_run(dataset, *, config_class, validator, worker, replay=True):
    """Check all shot identities/counts and replay the first batch of every point."""
    metadata = dataset.metadata
    if metadata["status"] != "sampling_complete":
        raise ValueError("Only completed runs can pass the audit")
    config = config_class(**metadata["resolved_config"])
    if config.config_hash != metadata["config_hash"]:
        raise ValueError("Resolved configuration hash mismatch")
    expected = {
        (t.config_id, t.batch_id): t
        for t in batch_tasks(config, metadata["experiment_id"])
    }
    totals, seen, replayed = {}, set(), 0
    for path in dataset.shards:
        frame = pd.read_parquet(path)
        validator(frame)
        if len(frame[["config_id", "batch_id"]].drop_duplicates()) != 1:
            raise ValueError("Shard contains multiple batches")
        key = (frame.config_id.iloc[0], int(frame.batch_id.iloc[0]))
        if key in seen or key not in expected:
            raise ValueError("Duplicate or unexpected batch")
        seen.add(key)
        task = expected[key]
        ordered = frame.sort_values("shot_index").reset_index(drop=True)
        np.testing.assert_array_equal(
            ordered.shot_index, np.arange(task.offset, task.offset + task.shots)
        )
        for name, value in (
            ("experiment_id", task.experiment_id),
            ("batch_seed", task.seed),
            ("distance", task.distance),
            ("physical_error_rate", task.physical_error_rate),
        ):
            if not (frame[name] == value).all():
                raise ValueError(f"Invalid batch {name}")
        counts = totals.setdefault(task.config_id, [0, 0, 0])
        counts[0] += len(frame)
        counts[1] += int(frame.ordinary_logical_error.sum())
        counts[2] += int(frame.comparative_logical_error.sum())
        if replay and task.batch_id == 0:
            repeated = worker(task)[ordered.columns]
            pd.testing.assert_frame_equal(
                ordered, repeated, check_dtype=False, check_exact=True
            )
            replayed += 1
    if seen != set(expected):
        raise ValueError("Missing batches")
    summary = pd.read_parquet(dataset.run_directory / "summary.parquet")
    if summary.config_id.duplicated().any() or set(summary.config_id) != set(totals):
        raise ValueError("Incomplete or duplicated summary")
    for row in summary.itertuples():
        if [row.shots, row.ordinary_failures, row.comparative_failures] != totals[
            row.config_id
        ]:
            raise ValueError("Summary differs from raw shots")
    total = sum(v[0] for v in totals.values())
    if (
        total != metadata["completed_shots"]
        or len(seen) != metadata["completed_batches"]
    ):
        raise ValueError("Manifest counts differ from shards")
    drift = [
        name
        for name, digest in metadata["source_hashes"].items()
        if not (PROJECT_ROOT / name).exists()
        or hashlib.sha256((PROJECT_ROOT / name).read_bytes()).hexdigest() != digest
    ]
    result = dict(
        passed=True,
        shots=total,
        batches=len(seen),
        replayed_batches=replayed,
        source_drift=drift,
        exact_source_match=not drift,
    )
    write_json(dataset.run_directory / "audit.json", result)
    return result
