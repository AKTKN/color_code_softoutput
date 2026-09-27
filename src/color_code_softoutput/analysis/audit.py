"""Independent raw-shard accounting and deterministic replay checks."""
from dataclasses import asdict
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .dataset import Phase2ADataset
from ..simulation.config import Phase2ATestConfig, batch_tasks, PROJECT_ROOT
from ..simulation.provenance import repository_state, source_hashes, write_json
from ..simulation.sampling import sample_batch
from ..simulation.storage import validate_shots


def audit_run(dataset: Phase2ADataset, *, replay: bool = True, check_current_sources: bool = True) -> dict:
    """Validate every shard and independently recompute counts with bounded memory.

    Args:
        dataset: Saved run to audit.
        replay: Recompute one complete saved batch with its original seed.
        check_current_sources: Require current external commits/status and package hashes.
    Returns:
        Audit counts and replay status, also saved as audit.json.
    Raises:
        AssertionError/ValueError: Any schema, identity, count or metric mismatch.
    Notes:
        Replays the same batch size because Stim does not promise prefix invariance
        across different sample sizes. This is a validation replay, not new statistics.
    """
    config = Phase2ATestConfig(**dataset.metadata["resolved_config"])
    experiment_id = dataset.run_directory.name
    expected = {(t.config_id,t.batch_id):t for t in batch_tasks(config,experiment_id)}
    seen = set()
    counts = {}
    disagreements = 0
    first_frame = first_task = None
    for path in dataset.shards:
        frame = pq.read_table(path).to_pandas()
        validate_shots(frame)
        identities = frame[["config_id","batch_id"]].drop_duplicates()
        if len(identities) != 1:
            raise ValueError("Shard must contain exactly one batch")
        key = tuple(identities.iloc[0])
        if key in seen or key not in expected:
            raise ValueError("Duplicate or unexpected batch")
        seen.add(key)
        task = expected[key]
        if len(frame) != task.shots:
            raise ValueError("Wrong batch length")
        for column,value in (("experiment_id",experiment_id),("batch_seed",task.seed),
                             ("distance",task.distance),("physical_error_rate",task.physical_error_rate)):
            if not (frame[column] == value).all():
                raise ValueError(f"Wrong batch metadata: {column}")
        np.testing.assert_array_equal(frame.shot_index,np.arange(task.offset,task.offset+task.shots))
        record = counts.setdefault(task.config_id,dict(config_id=task.config_id,distance=task.distance,
            physical_error_rate=task.physical_error_rate,shots=0,ordinary_failures=0,comparative_failures=0))
        record["shots"] += len(frame)
        for decoder in ("ordinary","comparative"):
            record[f"{decoder}_failures"] += int(np.count_nonzero(frame[f"{decoder}_prediction"].to_numpy() ^ frame.actual_observable.to_numpy()))
        disagreements += int(np.count_nonzero(frame.ordinary_prediction != frame.comparative_prediction))
        if first_frame is None:
            first_frame,first_task = frame,task
    if seen != set(expected):
        raise ValueError("Incomplete run: missing batches")
    raw_summary = pd.DataFrame(counts.values()).sort_values("config_id").reset_index(drop=True)
    saved = pd.read_parquet(dataset.run_directory / "summary.parquet").sort_values("config_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(raw_summary[saved.columns],saved,check_dtype=False)
    if check_current_sources:
        for name in ("PyMatching","color-code-stim"):
            if repository_state(PROJECT_ROOT / "external_libs" / name) != dataset.metadata["repositories"][name]:
                raise ValueError(f"Current repository state differs: {name}")
        if source_hashes() != dataset.metadata["source_hashes"]:
            raise ValueError("Current package source differs from sampling manifest")
    if replay:
        repeated = sample_batch(first_task)
        pd.testing.assert_frame_equal(first_frame.sort_index(axis=1),repeated.sort_index(axis=1),check_dtype=False)
    result = dict(status="passed",shards=len(seen),shots=int(raw_summary.shots.sum()),
                  hard_disagreements=disagreements,replay_batch=asdict(first_task) if replay else None,
                  current_sources_checked=check_current_sources)
    write_json(dataset.run_directory / "audit.json",result)
    return result
