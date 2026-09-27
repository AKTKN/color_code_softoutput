"""Adaptive, storage-agnostic scheduling for the staged YAML workflow.

Ready points are visited round robin. A point has only its calibration chunk
in flight until that chunk completes; afterwards it may occupy several slots.
Completed arrays are handed to ``on_result`` and are never retained here.
"""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
import hashlib
import math
from multiprocessing import get_context
from time import monotonic
from typing import Callable, Sequence

import numpy as np

from .config import ChunkingSettings, WorkflowConfig
from .task import ResolvedPoint
from .worker import WorkerInput, WorkerResult, run_chunk


def chunk_seed(master_seed: int, point_id: str, chunk_id: int) -> int:
    """Stable uint64 seed for a given point and chunk identity.

    Runtime-dependent chunk partitioning can change the sample stream even
    though seeds are stable once chunk IDs have been assigned.
    """
    if type(master_seed) is not int or master_seed < 0 or type(chunk_id) is not int or chunk_id < 0:
        raise ValueError("master_seed and chunk_id must be nonnegative integers")
    if not isinstance(point_id, str) or not point_id:
        raise ValueError("point_id must be a nonempty string")
    digest = hashlib.sha256(point_id.encode("utf-8")).digest()
    words = np.frombuffer(digest, dtype="<u4").tolist()
    return int(np.random.SeedSequence([master_seed, *words, chunk_id]).generate_state(1, dtype=np.uint64)[0])


def update_seconds_per_shot(previous: float | None, elapsed_seconds: float,
                            shot_count: int, alpha: float,
                            fallback: float) -> float:
    """EWMA of observed seconds/shot; retain/fallback on invalid timing.

    Zero or sub-resolution timing is not treated as infinite throughput.
    The fallback is target_chunk_seconds / calibration_shots.
    """
    if shot_count <= 0 or not 0 < alpha <= 1 or not math.isfinite(fallback) or fallback <= 0:
        raise ValueError("invalid throughput parameters")
    valid = math.isfinite(elapsed_seconds) and elapsed_seconds > 0
    observed = elapsed_seconds / shot_count if valid else 0.0
    if not math.isfinite(observed) or observed <= 0:
        return previous if previous is not None else fallback
    return observed if previous is None else alpha * observed + (1 - alpha) * previous


def adaptive_chunk_shots(seconds_per_shot: float, remaining_unscheduled_shots: int,
                         settings: ChunkingSettings, *, buffer_shots: int | None = None) -> int:
    """Round target/sps, clamp to chunk bounds and remaining shots.

    ``buffer_shots`` is an optional per-result memory cap from simulation
    settings. It may be smaller than min_chunk_shots.
    """
    if remaining_unscheduled_shots <= 0:
        return 0
    if not math.isfinite(seconds_per_shot) or seconds_per_shot <= 0:
        raise ValueError("seconds_per_shot must be positive and finite")
    upper = settings.max_chunk_shots
    if buffer_shots is not None:
        if buffer_shots <= 0:
            raise ValueError("buffer_shots must be positive")
        upper = min(upper, buffer_shots)
    lower = min(settings.min_chunk_shots, upper)
    ratio = settings.target_chunk_seconds / seconds_per_shot
    raw = upper if not math.isfinite(ratio) else round(ratio)
    return min(remaining_unscheduled_shots, max(lower, min(upper, raw)))


@dataclass(frozen=True)
class PointProgress:
    point_id: str
    total_shots: int
    next_shot_to_schedule: int
    completed_shots: int
    next_chunk_id: int
    seconds_per_shot: float | None
    calibrated: bool
    in_flight: int

    @property
    def remaining_shots(self) -> int:
        return self.total_shots - self.completed_shots


def estimate_eta_seconds(points: Sequence[PointProgress], workers: int) -> float | None:
    """Remaining estimated worker-seconds divided by available parallelism.

    Return None while any unfinished point has no timing observation. Since a
    calibrated point can have multiple chunks in flight, effective parallelism
    is min(workers, remaining shots), an optimistic capacity approximation.
    """
    remaining = [p for p in points if p.remaining_shots]
    if not remaining:
        return 0.0
    if workers <= 0 or any(p.seconds_per_shot is None or not math.isfinite(p.seconds_per_shot)
                           or p.seconds_per_shot <= 0 for p in remaining):
        return None
    cpu_seconds = sum(p.remaining_shots * p.seconds_per_shot for p in remaining)
    return cpu_seconds / min(workers, sum(p.remaining_shots for p in remaining))


def _duration(seconds: float) -> str:
    whole = max(0, round(seconds))
    hours, rem = divmod(whole, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def progress_line(points: Sequence[PointProgress], active_workers: int,
                  workers: int, elapsed_seconds: float) -> str:
    """One reusable progress format for the eventual runner."""
    completed = sum(p.completed_shots for p in points)
    total = sum(p.total_shots for p in points)
    done_points = sum(p.completed_shots == p.total_shots for p in points)
    eta = estimate_eta_seconds(points, workers)
    eta_text = "estimating..." if eta is None else f"~ {_duration(eta)}"
    return (f"{completed}/{total} shots ({100 * completed / total if total else 100:.1f}%), "
            f"workers {active_workers}/{workers}, points {done_points}/{len(points)}, "
            f"elapsed {_duration(elapsed_seconds)}, ETA {eta_text}")


@dataclass
class _PointState:
    point: ResolvedPoint
    next_shot_to_schedule: int = 0
    completed_shots: int = 0
    next_chunk_id: int = 0
    seconds_per_shot: float | None = None
    calibrated: bool = False
    in_flight: int = 0

    def snapshot(self) -> PointProgress:
        return PointProgress(self.point.point_id, self.point.shots, self.next_shot_to_schedule,
                             self.completed_shots, self.next_chunk_id, self.seconds_per_shot,
                             self.calibrated, self.in_flight)


def run_scheduler(config: WorkflowConfig, points: Sequence[ResolvedPoint],
                  on_result: Callable[[WorkerResult], None], *,
                  worker: Callable[[WorkerInput], WorkerResult] = run_chunk,
                  executor_factory: Callable = ProcessPoolExecutor,
                  reporter: Callable[[str], None] = print,
                  clock: Callable[[], float] = monotonic) -> tuple[PointProgress, ...]:
    """Run bounded jobs via spawn, delivering completed chunks to caller.

    The callback must consume/write each result before returning. Exceptions
    from workers or callback propagate; no scheduler-owned output is written.
    ``executor_factory`` and ``worker`` permit deterministic synthetic tests.
    """
    if len({p.point_id for p in points}) != len(points) or any(p.shots <= 0 for p in points):
        raise ValueError("points need unique IDs and positive shot counts")
    if any(p.shots != config.simulation.shots for p in points):
        raise ValueError("point shots must match simulation.shots")
    states = [_PointState(p) for p in points]
    started = clock()
    cursor = 0
    pending = {}

    def snapshots() -> tuple[PointProgress, ...]:
        return tuple(state.snapshot() for state in states)

    def fill(executor) -> None:
        nonlocal cursor
        while len(pending) < config.simulation.workers:
            selected = None
            for step in range(len(states)):
                index = (cursor + step) % len(states)
                state = states[index]
                if state.next_shot_to_schedule < state.point.shots and (state.calibrated or not state.in_flight):
                    selected = index
                    break
            if selected is None:
                break
            state = states[selected]
            cursor = (selected + 1) % len(states)
            remaining = state.point.shots - state.next_shot_to_schedule
            if not state.calibrated:
                count = min(config.chunking.calibration_shots, remaining,
                            config.simulation.buffer_shots)
            else:
                count = adaptive_chunk_shots(state.seconds_per_shot, remaining, config.chunking,
                                             buffer_shots=config.simulation.buffer_shots)
            task = WorkerInput(state.point.point_id, state.next_chunk_id,
                               state.next_shot_to_schedule, count,
                               chunk_seed(config.simulation.master_seed, state.point.point_id,
                                          state.next_chunk_id), state.point)
            future = executor.submit(worker, task)
            pending[future] = (state, task)
            state.next_shot_to_schedule += count
            state.next_chunk_id += 1
            state.in_flight += 1

    with executor_factory(max_workers=config.simulation.workers, mp_context=get_context("spawn")) as executor:
        fill(executor)
        if config.simulation.verbose:
            reporter(progress_line(snapshots(), len(pending), config.simulation.workers, clock() - started))
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                state, task = pending.pop(future)
                result = future.result()
                if (result.point_id, result.chunk_id, result.shot_start, result.shot_count) != (
                        task.point_id, task.chunk_id, task.shot_start, task.shot_count):
                    raise ValueError("worker result identity/interval mismatch")
                state.in_flight -= 1
                state.completed_shots += task.shot_count
                fallback = config.chunking.target_chunk_seconds / config.chunking.calibration_shots
                state.seconds_per_shot = update_seconds_per_shot(
                    state.seconds_per_shot, result.elapsed_seconds, task.shot_count,
                    config.chunking.throughput_ema_alpha, fallback)
                state.calibrated = True
                on_result(result)
                fill(executor)
                if config.simulation.verbose:
                    reporter(progress_line(snapshots(), len(pending), config.simulation.workers,
                                           clock() - started))
    return snapshots()
