"""Fixed Lee-style paired experiment, implemented during Phase 2B."""
import argparse
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from time import perf_counter
import pandas as pd
from ..simulation.config import Phase2ATestConfig, batch_tasks
from ..simulation.parallel_runner import completed_batches
from ..simulation.provenance import create_metadata, write_json, archive_sources
from ..simulation.storage import write_shard


@dataclass(frozen=True)
class RunResult:
    """Completed run location, exact row count, batches and elapsed wall seconds."""
    run_directory: Path
    shots: int
    batches: int
    elapsed_seconds: float


def run_experiment(config: Phase2ATestConfig, *, analyze: bool = False) -> RunResult:
    """Execute the fixed grid with bounded memory and durable paired batch shards.

    Args:
        config: Infrastructure and fixed-code grid settings.
        analyze: Run standard publication analysis after sampling if True.
    Returns:
        Structured result with a timezone-aware timestamped run path.
    Raises:
        FileExistsError: Timestamp collision; existing results are never overwritten.
        Exception: Sampling/storage failures; atomic completed shards are retained.
    Notes:
        Resume is deliberately deferred. Failed runs record their exception and
        can be inspected; restart uses a new directory and identical seeds.
    """
    timestamp = datetime.now().astimezone()
    experiment_id = timestamp.strftime("%Y%m%d_%H%M%S_phase2a_test")
    directory = config.output_root / experiment_id
    directory.mkdir(parents=True, exist_ok=False)
    for name in ("shots", "figures", "logs"):
        (directory / name).mkdir()
    manifest = create_metadata(config, timestamp)
    archive_sources(directory / "source_snapshot.zip", manifest["source_hashes"])
    write_json(directory / "metadata.json", manifest)
    write_json(directory / "resolved_config.json", config.resolved())
    logger = logging.getLogger(f"color_code_softoutput.{experiment_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handlers = [logging.FileHandler(directory / "logs/run.log")]
    if config.verbose:
        handlers.append(logging.StreamHandler())
    for handler in handlers:
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
    start = perf_counter()
    total = len(config.distances)*len(config.probabilities)*config.shots_per_point
    done = batches = 0
    summaries = {}
    try:
        for task, frame in completed_batches(batch_tasks(config, experiment_id), config.num_workers):
            name = f"{task.config_id}_batch{task.batch_id:06d}.parquet"
            if len(frame) != task.shots:
                raise ValueError("Worker returned wrong row count")
            write_shard(frame, directory / "shots" / name, config.config_hash)
            point = summaries.setdefault(task.config_id, dict(config_id=task.config_id, distance=task.distance,
                physical_error_rate=task.physical_error_rate, shots=0, ordinary_failures=0, comparative_failures=0))
            point["shots"] += len(frame)
            for decoder in ("ordinary", "comparative"):
                point[f"{decoder}_failures"] += int(frame[f"{decoder}_logical_error"].sum())
            done += len(frame)
            batches += 1
            elapsed = perf_counter()-start
            logger.info("shots %d/%d; batches %d; %s %d/%d; elapsed %.1fs; %.0f shots/s; ETA %.1fs; workers %d",
                        done, total, batches, task.config_id, point["shots"], config.shots_per_point,
                        elapsed, done/elapsed, (total-done)*elapsed/done, config.num_workers)
        pd.DataFrame(summaries.values()).sort_values(["distance", "physical_error_rate"]).to_parquet(directory / "summary.parquet", index=False)
        manifest.update(status="sampling_complete", completed_shots=done, completed_batches=batches,
                        elapsed_seconds=perf_counter()-start)
        write_json(directory / "metadata.json", manifest)
        if analyze:
            from ..analysis.workflow import standard_analysis
            standard_analysis(directory)
        return RunResult(directory, done, batches, manifest["elapsed_seconds"])
    except BaseException as exception:
        manifest.update(status="failed", failure=repr(exception), completed_shots=done,
                        elapsed_seconds=perf_counter()-start)
        write_json(directory / "metadata.json", manifest)
        raise
    finally:
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()


def main() -> None:
    """Parse fixed-experiment infrastructure flags and print the saved run path.

    Notes:
        --smoke uses 128 shots per point unless --shots explicitly overrides it.
        Code architecture, distance list and probability grid stay fixed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shots", type=int)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260912)
    parser.add_argument("--output-root", type=Path, default=Phase2ATestConfig().output_root)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    args = parser.parse_args()
    config = Phase2ATestConfig(shots_per_point=args.shots if args.shots is not None else (128 if args.smoke else 100000),
                              batch_size=args.batch_size, num_workers=args.workers,
                              master_seed=args.seed, output_root=args.output_root, verbose=not args.quiet)
    result = run_experiment(config, analyze=args.analyze)
    print(result)


if __name__ == "__main__":
    main()
