"""Paired adaptive benchmark contract and saved diagnostic checks."""

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.analysis.adaptive_benchmark import AdaptiveBenchmarkRun, save_report
from color_code_softoutput.simulation.adaptive_benchmark import run_paired, run_ablation


def test_paired_smoke_and_weight_roundtrip(tmp_path):
    basis = "original_dem"
    root = run_paired(output_root=tmp_path, shots=8, batch_shots=3, seed=13, weight_basis=basis)
    run = AdaptiveBenchmarkRun(root)
    assert run.manifest["schema_version"] == "adaptive_v2"
    assert set(run.manifest["decode_seconds"]) == {
        "baseline", "color_correlated", "relift", "perturbation"}
    assert run.manifest["batch_count"] == 3
    assert len(set(run.manifest["batch_seeds"])) == 3
    assert set(run.metrics) >= {"color_correlated_run", "relift_run", "baseline_error"}
    for name in ("color_correlated_run", "relift_run"):
        table = pq.read_table(root / f"{name}.parquet")
        assert table.schema == pa.schema([pa.field("shot_index", pa.int64(), nullable=False),
                                          pa.field(name, pa.uint8(), nullable=False)])
        assert table.column("shot_index").to_pylist() == list(range(8))
    for name, (weights, saved_basis, selected) in run.weights.items():
        assert saved_basis == basis
        assert weights.shape[-1] == 8
        np.testing.assert_allclose(np.min(weights, axis=(0, 1)), selected)
    assert sum(run.by_class("relift")["shots"]) == 8
    assert sum(run.by_class("color_correlated")["shots"]) == 8
    np.testing.assert_array_equal(run.metrics["color_correlated_run"], run.metrics["relift_run"])
    assert sum(run.overall_relift()["unique_stage2_problems_per_shot"].values()) == 8
    assert np.all(run.metrics["relift_total_mwpm_calls"] ==
                  6 + run.metrics["relift_extra_stage2_calls"])
    assert np.all(run.metrics["relift_pairwise_baseline_equal"] <= 6)
    assert np.all(run.metrics["relift_selected_kind"] <= 2)
    assert np.all(run.metrics["relift_extra_stage2_calls"][run.metrics["relift_run"] == 0] == 0)
    assert np.all(run.metrics["relift_cache_skips"] <=
                  run.metrics["relift_aliases_to_baseline"] +
                  run.metrics["relift_aliases_to_candidate"])
    summary = run.point_summary()
    assert set(summary.strategy) == {"baseline", "color_correlated", "relift", "perturbation"}
    assert set(summary.weight_basis) == {basis}
    assert (summary.mean_actual_mwpm_calls <= summary.nominal_max_mwpm_calls).all()
    assert np.all(run.metrics["color_correlated_extra_mwpm_calls"][run.metrics["color_correlated_run"] == 0] == 0)
    assert np.all(run.metrics["relift_all_color_new"] <= 3)
    assert np.all(run.metrics["perturbation_selected_member"] < 3)
    assert np.all(run.metrics["perturbation_unique_stage1"] <= 9)
    assert np.all(run.metrics["perturbation_unique_corrections"] <= 9)
    assert run.overall_relift()["all_color_new_syndrome_fraction"] <= 1
    save_report([root], tmp_path / "report")
    assert (tmp_path / "report" / f"ler_vs_p_{basis}.png").exists()
    assert (tmp_path / "report" / "points.csv").exists()


def test_ablation_small_grid(tmp_path):
    paths = run_ablation(output_root=tmp_path, shots=2, distances=(3,),
        physical_error_rates=(.01,), bases=("original_dem",), ensemble_sizes=(2, 4),
        alphas=(.25, .5), seed=21)
    assert len(paths) == 4
    assert {(AdaptiveBenchmarkRun(path).manifest["ensemble_size"],
             AdaptiveBenchmarkRun(path).manifest["alpha"]) for path in paths} == {
                 (2, .25), (2, .5), (4, .25), (4, .5)}


def test_paired_stage2_basis_is_rejected_before_creating_a_run(tmp_path):
    with pytest.raises(ValueError, match="requires original_dem"):
        run_paired(output_root=tmp_path, shots=2, weight_basis="stage2")
    assert list(tmp_path.iterdir()) == []
