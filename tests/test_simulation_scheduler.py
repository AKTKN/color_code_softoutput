"""Synthetic, sleep-free checks for the adaptive scheduler."""

from concurrent.futures import Future
import math

import pytest

from color_code_softoutput.simulation import scheduler
from color_code_softoutput.simulation.config import (ChunkingSettings, DecoderSettings,
    SimulationSettings, SweepSettings, WorkflowConfig, batch_seed)
from color_code_softoutput.simulation.task import ResolvedPoint
from color_code_softoutput.simulation.worker import WorkerResult


def config(*, workers=2, shots=20, verbose=False, calibration=2, target=4,
           minimum=1, maximum=10, alpha=.5, buffer=10):
    return WorkflowConfig(SimulationSettings("unused", shots, workers, 42, buffer, verbose),
        ChunkingSettings(calibration, target, minimum, maximum, alpha),
        SweepSettings((3,), (.05,), ("bitflip",), (1,), ("tri",), ("tri_optimal",)),
        (), (DecoderSettings("ordinary", (), ()),))


def point(identity, shots=20):
    return ResolvedPoint(identity, "ordinary", 3, .05, "bitflip", 1,
                         "tri", "tri_optimal", shots, (), (), ())


def synthetic_spawn_worker(task):
    """Picklable process worker that exercises the real spawn executor."""
    return WorkerResult(task.point_id, task.chunk_id, task.shot_start,
                        task.shot_count, .25 * task.shot_count, {})


class FakeExecutor:
    """Submit records jobs; selected futures complete only when fake_wait runs."""

    instances = []

    def __init__(self, *, max_workers, mp_context):
        assert mp_context.get_start_method() == "spawn"
        self.max_workers = max_workers
        self.jobs = {}
        self.submitted = []
        self.max_pending = 0
        self.completion_order = []
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, worker, task):
        future = Future()
        self.jobs[future] = task
        self.submitted.append(task)
        self.max_pending = max(self.max_pending, len(self.jobs))
        return future

    def finish(self, future):
        task = self.jobs.pop(future)
        # p0 is fast; p1 is slow. Calibration and all subsequent chunks
        # use synthetic durations, independent of wall clock.
        sps = .1 if task.point_id == "p0" else 4.0
        future.set_result(WorkerResult(task.point_id, task.chunk_id,
            task.shot_start, task.shot_count, sps * task.shot_count, {}))
        self.completion_order.append((task.point_id, task.chunk_id))


def fake_wait(futures, *, return_when):
    executor = FakeExecutor.instances[-1]
    # Finish the newest p0 job first to prove that completion order does not
    # assign intervals, and a newly freed slot is filled before p1 finishes.
    chosen = next((f for f in reversed(tuple(executor.jobs))
                   if f in futures and executor.jobs[f].point_id == "p0"), None)
    if chosen is None:
        chosen = next(iter(futures))
    executor.finish(chosen)
    return {chosen}, set(futures) - {chosen}


def test_chunk_formula_and_ema():
    settings = config().chunking
    assert scheduler.update_seconds_per_shot(None, 2, 2, .5, 1) == 1
    assert scheduler.update_seconds_per_shot(1, 6, 2, .25, 1) == 1.5
    assert scheduler.update_seconds_per_shot(None, 0, 2, .5, .75) == .75
    assert scheduler.update_seconds_per_shot(1, math.nan, 2, .5, .75) == 1
    assert scheduler.adaptive_chunk_shots(.1, 100, settings) == 10  # fast grows, max clamp
    assert scheduler.adaptive_chunk_shots(100, 100, settings) == 1  # slow shrinks, min clamp
    assert scheduler.adaptive_chunk_shots(.1, 3, settings) == 3
    assert scheduler.adaptive_chunk_shots(.1, 100, settings, buffer_shots=3) == 3
    with pytest.raises(ValueError):
        scheduler.adaptive_chunk_shots(math.nan, 10, settings)


def test_seed_is_stable_and_identity_dependent():
    a = scheduler.chunk_seed(42, "point", 0)
    assert a == batch_seed(42, "point", 0)
    assert a == scheduler.chunk_seed(42, "point", 0)
    assert len({a, scheduler.chunk_seed(43, "point", 0),
                scheduler.chunk_seed(42, "other", 0),
                scheduler.chunk_seed(42, "point", 1)}) == 4


def test_eta_and_progress():
    uncalibrated = scheduler.PointProgress("p", 10, 2, 2, 1, None, False, 0)
    assert scheduler.estimate_eta_seconds((uncalibrated,), 2) is None
    assert "ETA: estimating..." in scheduler.progress_line((uncalibrated,), 0, 2, 1)
    early = scheduler.PointProgress("p", 10, 2, 2, 1, 2., True, 0)
    late = scheduler.PointProgress("p", 10, 8, 8, 2, 2., True, 0)
    assert scheduler.estimate_eta_seconds((early,), 2) == 8
    assert scheduler.estimate_eta_seconds((late,), 2) == 2
    assert "ETA: ~ 00:00:08" in scheduler.progress_line((early,), 1, 2, 1)


@pytest.mark.parametrize("verbose", [False, True])
def test_scheduler_intervals_fairness_refill_and_reporting(monkeypatch, verbose):
    FakeExecutor.instances.clear()
    monkeypatch.setattr(scheduler, "wait", fake_wait)
    lines = []
    received = []

    def consume(result):
        received.append(result)
        executor = FakeExecutor.instances[-1]
        # At first completion, p1 calibration is still active. The slot is
        # refilled with p0 normal work immediately, without a wave barrier.
        if len(received) == 1:
            assert result.point_id == "p0"
            assert any(t.point_id == "p1" and t.chunk_id == 0 for t in executor.jobs.values())

    final = scheduler.run_scheduler(config(verbose=verbose),
        (point("p0"), point("p1")), consume,
        executor_factory=FakeExecutor, reporter=lines.append, clock=lambda: 0.)
    executor = FakeExecutor.instances[-1]
    assert executor.max_pending <= 2
    assert executor.submitted[0].point_id == "p0"
    assert executor.submitted[1].point_id == "p1"
    assert all(t.shot_count == 2 for t in executor.submitted[:2])
    assert executor.submitted[2].point_id == "p0"  # refill before p1 completes
    assert executor.submitted[2].shot_count == 10
    assert executor.completion_order.index(("p1", 0)) > executor.completion_order.index(("p0", 1))
    for identity in ("p0", "p1"):
        tasks = [t for t in executor.submitted if t.point_id == identity]
        assert tasks[0].shot_count == 2
        assert all(t.chunk_id == i for i, t in enumerate(tasks))
        assert [t.shot_start for t in tasks] == [0] + [
            t.shot_start + t.shot_count for t in tasks[:-1]]
        assert tasks[-1].shot_start + tasks[-1].shot_count == 20
        assert all(t.seed == scheduler.chunk_seed(42, identity, t.chunk_id) for t in tasks)
    assert all(p.completed_shots == p.total_shots == 20 and p.remaining_shots == 0 for p in final)
    assert len(received) == len(executor.submitted)
    if verbose:
        assert len(lines) == len(received) + 1
        assert "ETA: estimating..." in lines[0]
        assert "40/40 shots" in lines[-1] and "points 2/2" in lines[-1]
    else:
        assert lines == []


def test_single_point_uses_all_workers_after_calibration(monkeypatch):
    FakeExecutor.instances.clear()
    monkeypatch.setattr(scheduler, "wait", fake_wait)
    scheduler.run_scheduler(config(workers=3, shots=30), (point("p0", 30),),
                            lambda _: None, executor_factory=FakeExecutor)
    executor = FakeExecutor.instances[-1]
    assert executor.max_pending == 3
    assert [t.shot_count for t in executor.submitted[:3]] == [2, 10, 10]


def test_round_robin_with_one_worker(monkeypatch):
    FakeExecutor.instances.clear()
    monkeypatch.setattr(scheduler, "wait", fake_wait)
    scheduler.run_scheduler(config(workers=1, shots=8),
        (point("p0", 8), point("p1", 8)), lambda _: None,
        executor_factory=FakeExecutor)
    sequence = [task.point_id for task in FakeExecutor.instances[-1].submitted]
    assert sequence[:4] == ["p0", "p1", "p0", "p1"]


def test_real_spawn_executor_smoke():
    received = []
    result = scheduler.run_scheduler(config(workers=2, shots=5),
        (point("spawn", 5),), received.append, worker=synthetic_spawn_worker)
    assert sum(chunk.shot_count for chunk in received) == 5
    assert result[0].completed_shots == 5
