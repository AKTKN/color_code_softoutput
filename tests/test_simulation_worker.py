"""Tiny contract checks for the YAML workflow's isolated worker."""

import numpy as np
import pytest

from color_code_softoutput.simulation import worker
from color_code_softoutput.simulation.task import ResolvedPoint


def point(correlated=False, *, identity="p", shots=8, weight_basis="stage2"):
    if correlated and weight_basis == "stage2":
        weight_basis = "original_dem"
    return ResolvedPoint(identity, "ordinary-label", 3, .05, "bitflip", 1,
                         "tri", "tri_optimal", shots, (),
                         (("enable_colorcorrelated_decoding", correlated),
                          ("color_correlated_weight_basis", weight_basis)), ())


def test_observable_failure_reduction():
    np.testing.assert_array_equal(
        worker.logical_errors(np.array([0, 1, 1]), np.array([0, 0, 1]), 3),
        [False, True, False])
    np.testing.assert_array_equal(
        worker.logical_errors(np.array([[0, 0], [1, 0], [1, 1]]),
                              np.array([[0, 0], [0, 0], [1, 0]]), 3),
        [False, True, True])


@pytest.mark.parametrize("baseline,selected,expected", [
    (3., 2., 1), (3., 3., 0), (3., 4., 0),
])
def test_common_prior_comparison(baseline, selected, expected):
    weights = np.full((1, 12, 1), 10.)
    weights[0, :3, 0] = baseline
    weights[0, 3, 0] = selected
    best = min(baseline, selected)
    extra = {"candidate_weights": weights, "weights": np.array([best]),
             "candidate_generation_weights": np.full((1, 12, 1), -1e9)}
    assert worker.better_common_prior_weight(extra, 1).tolist() == [expected]


def test_common_prior_comparison_ignores_unrun_candidates():
    weights = np.full((1, 12, 1), np.inf)
    weights[0, :3, 0] = [3., 4., 5.]
    weights[0, 4, 0] = 2.
    extra = {"candidate_weights": weights, "weights": np.array([2.])}
    assert worker.better_common_prior_weight(extra, 1).tolist() == [1]


def test_chunk_same_shots_metrics_and_interval(monkeypatch):
    seen = []

    class FakeCode:
        def __init__(self, correlated):
            self.correlated = correlated

        def sample(self, count, seed):
            seen.append(("sample", count, seed))
            return np.array([[0], [1], [0]], dtype=bool), np.array([0, 0, 1], dtype=bool)

        def decode(self, detectors, **options):
            seen.append(("decode", self.correlated, detectors.copy(), options))
            if not self.correlated:
                return np.array([0, 1, 0], dtype=bool)
            weights = np.full((1, 12, 3), 5.)
            weights[0, 3] = [4., 4., 4.]
            return np.array([0, 0, 1], dtype=bool), {
                "candidate_weights": weights, "weights": np.array([4., 4., 4.]),
                "candidate_generation_weights": np.full_like(weights, -100.),
                "color_correlated_run": np.array([0, 1, 2], dtype=np.int8),
            }

    monkeypatch.setattr(worker, "_codes", lambda _: worker._CodePair(FakeCode(True), FakeCode(False)))
    p = point(True, shots=10)
    result = worker.run_chunk(worker.WorkerInput("p", 2, 4, 3, 71, p))
    assert (result.point_id, result.chunk_id, result.shot_start, result.shot_count) == ("p", 2, 4, 3)
    assert result.elapsed_seconds >= 0
    assert [x[0] for x in seen] == ["sample", "decode", "decode"]
    np.testing.assert_array_equal(seen[1][2], seen[2][2])
    assert result.metrics["logical_error"].tolist() == [False, False, False]
    assert result.metrics["default_logical_error"].tolist() == [False, True, True]
    assert result.metrics["effect_by_color_correlated_decoding"].tolist() == [0, 1, 1]
    assert result.metrics["better_weight_by_color_correlated_decoding"].tolist() == [1, 1, 1]
    assert result.metrics["color_correlated_run"].tolist() == [0, 1, 2]
    assert result.metrics["effect_by_color_correlated_decoding"].dtype == np.uint8


def test_cache_bounded(monkeypatch):
    monkeypatch.setattr(worker, "_construct", lambda p: worker._CodePair(object(), None))
    worker._CODE_CACHE.clear()
    try:
        for i in range(worker.CACHE_MAXSIZE + 3):
            worker._codes(ResolvedPoint(str(i), "label", 3, .01 + i / 100,
                "bitflip", 1, "tri", "tri_optimal", 8, (), (), ()))
        assert len(worker._CODE_CACHE) == worker.CACHE_MAXSIZE
    finally:
        worker._CODE_CACHE.clear()


@pytest.mark.parametrize("correlated,weight_basis", [
    (False, "stage2"), (False, "original_dem"),
    (True, "stage2"), (True, "original_dem"),
])
def test_real_tiny_worker(correlated, weight_basis):
    worker._CODE_CACHE.clear()
    p = point(correlated, identity=f"real-{correlated}-{weight_basis}",
              shots=2, weight_basis=weight_basis)
    out = worker.run_chunk(worker.WorkerInput(p.point_id, 0, 0, 2, 3, p))
    expected = {"logical_error"}
    if correlated:
        expected |= {"default_logical_error", "better_weight_by_color_correlated_decoding",
                     "effect_by_color_correlated_decoding", "color_correlated_run"}
    assert set(out.metrics) == expected
    assert all(arr.shape == (2,) for arr in out.metrics.values())
    if correlated:
        np.testing.assert_array_equal(out.metrics["effect_by_color_correlated_decoding"],
            (out.metrics["default_logical_error"] & ~out.metrics["logical_error"]).astype(np.uint8))
        assert out.metrics["color_correlated_run"].dtype == np.uint8
        assert np.all(out.metrics["color_correlated_run"] <= 2)
    worker._CODE_CACHE.clear()


@pytest.mark.parametrize("mode", ["relifting", "perturbation"])
@pytest.mark.parametrize("basis", ["stage2", "original_dem"])
def test_advanced_worker_reuses_internal_baseline(mode, basis):
    from color_code_stim import ColorCode
    from color_code_softoutput.simulation.noise import make_noise_model

    option = ({"enable_cross_color_relifting": True, "remove_non_edge_like_errors": False}
              if mode == "relifting" else
              {"enable_prior_perturbation": True, "perturbation_ensemble_size": 2,
               "perturbation_alpha": .25, "perturbation_seed": 11})
    options = option | {"color_correlated_weight_basis": basis, "temp_bdry_type": "Z"}
    p = ResolvedPoint(f"{mode}-{basis}", mode, 3, .01, "uniform", 3,
                      "tri", "tri_optimal", 2, (), tuple(sorted(options.items())), ())
    worker._CODE_CACHE.clear()
    task = worker.WorkerInput(p.point_id, 0, 0, 2, 31, p)
    out = worker.run_chunk(task)
    expected = {"logical_error", "default_logical_error",
                "better_weight_by_color_correlated_decoding",
                "effect_by_color_correlated_decoding"}
    if mode == "relifting":
        expected.add("relift_run")
    assert set(out.metrics) == expected
    configured = worker._construct(p).configured
    detectors, actual = configured.sample(2, seed=31)
    baseline_options = options | {"enable_cross_color_relifting": False,
                                  "enable_prior_perturbation": False}
    ordinary = ColorCode(d=3, rounds=3, circuit_type="tri", cnot_schedule="tri_optimal",
                         noise_model=make_noise_model("uniform", .01), **baseline_options)
    ordinary_fail = worker.logical_errors(ordinary.decode(detectors), actual, 2)
    np.testing.assert_array_equal(out.metrics["default_logical_error"], ordinary_fail)
    np.testing.assert_array_equal(out.metrics["effect_by_color_correlated_decoding"],
        (ordinary_fail & ~out.metrics["logical_error"]).astype(np.uint8))
    assert out.metrics["better_weight_by_color_correlated_decoding"].dtype == np.uint8
    worker._CODE_CACHE.clear()
