"""Same-shot storage and analysis for the original stage-2 SWIM metric."""

import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.analysis.workflow_soft_output import WorkflowSoftOutputRun
from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.runner import run_experiment


def config(tmp_path, decoders):
    return parse_workflow_config({
        "simulation": {"output_root": str(tmp_path), "shots": 4, "workers": 1,
                       "master_seed": 42, "buffer_shots": 2, "verbose": False},
        "chunking": {"calibration_shots": 2, "target_chunk_seconds": .1,
                     "min_chunk_shots": 1, "max_chunk_shots": 2,
                     "throughput_ema_alpha": .5},
        "sweep": {"distance": 3, "physical_error_rate": .05,
                  "noise_model": "bitflip", "rounds": 1,
                  "circuit_type": "tri", "cnot_schedule": "tri_optimal"},
        "color_code_options": {"temp_bdry_type": "Z"},
        "decoders": decoders,
    })


def test_ensemble_swim_files_and_analysis(tmp_path):
    scored = {"compute_swim_distance": True}
    decoders = [
        {"type": "concat_mwpm", "decode_options": scored},
        {"type": "perturbation", "options": {"enable_prior_perturbation": True,
            "perturbation_ensemble_size": 2, "perturbation_alpha": .2,
            "perturbation_seed": 1}, "decode_options": scored},
        {"type": "color_correlated", "options": {"enable_colorcorrelated_decoding": True,
            "color_correlated_b": 2}, "decode_options": scored},
        {"type": "relifting", "options": {"enable_cross_color_relifting": True,
            "remove_non_edge_like_errors": False}, "decode_options": scored},
    ]
    root = run_experiment(config(tmp_path, decoders), reporter=lambda _: None)
    for directory in root.glob("decoder_type=*,*"):
        table = pq.read_table(directory / "swim_distance.parquet")
        assert table.column("shot_index").to_pylist() == list(range(4))
        assert np.isfinite(table.column("swim_distance").to_numpy()).all()
    run = WorkflowSoftOutputRun(root)
    figure, histogram = run.plot_distribution(
        filter={"distance": 3}, group_by=("decoder_type",), bins=5)
    assert histogram.groupby("decoder_type").shots.sum().to_dict() == {
        name: 4 for name in ("concat_mwpm", "perturbation", "color_correlated", "relifting")}
    plt.close(figure)
    figure, curves = run.plot_postselection(group_by=("decoder_type",))
    assert set(curves.decoder_type) == set(histogram.decoder_type)
    assert (curves.groupby("decoder_type").first().abort_rate == 0).all()
    plt.close(figure)


def test_comparative_gap_file_and_swim_scope_preflight(tmp_path):
    comparative = [{"type": "concat_mwpm", "options": {"comparative_decoding": True}}]
    root = run_experiment(config(tmp_path, comparative), reporter=lambda _: None)
    path = next(root.glob("decoder_type=concat_mwpm,*")) / "logical_gap.parquet"
    assert pq.read_table(path).column("logical_gap").to_numpy().shape == (4,)
    run = WorkflowSoftOutputRun(root)
    figure, curve = run.plot_postselection(metric="logical_gap")
    assert curve.iloc[0].abort_rate == 0
    plt.close(figure)

    bad = config(tmp_path, [{"type": "concat_mwpm",
                            "decode_options": {"compute_swim_distance": True}}])
    # Open or incomplete circuit memory is outside the closed-memory topology.
    from dataclasses import replace
    bad = replace(bad, sweep=replace(bad.sweep, noise_model=("uniform",), rounds=(2,)))
    before = set(tmp_path.iterdir())
    with pytest.raises(ValueError, match="closed d-round"):
        run_experiment(bad)
    assert set(tmp_path.iterdir()) == before

    both = config(tmp_path, [{"type": "concat_mwpm",
                              "options": {"comparative_decoding": True},
                              "decode_options": {"compute_swim_distance": True}}])
    with pytest.raises(ValueError, match="cannot be combined"):
        run_experiment(both)
    assert set(tmp_path.iterdir()) == before


def test_circuit_swim_all_yaml_noise_models_and_ensembles(tmp_path):
    scored = {"compute_swim_distance": True}
    decoders = [
        {"type": "concat_mwpm", "decode_options": scored},
        {"type": "perturbation", "options": {"enable_prior_perturbation": True,
            "perturbation_ensemble_size": 2, "perturbation_alpha": .2,
            "perturbation_seed": 1}, "decode_options": scored},
        {"type": "color_correlated", "options": {"enable_colorcorrelated_decoding": True,
            "color_correlated_b": 2}, "decode_options": scored},
        {"type": "relifting", "options": {"enable_cross_color_relifting": True,
            "remove_non_edge_like_errors": False}, "decode_options": scored},
    ]
    from dataclasses import replace
    requested = config(tmp_path, decoders)
    requested = replace(requested,
        simulation=replace(requested.simulation, shots=2),
        sweep=replace(requested.sweep, noise_model=("bitflip", "depol", "uniform"),
                      rounds=(3,)))
    root = run_experiment(requested, reporter=lambda _: None)
    assert len(list(root.glob("decoder_type=*,*"))) == 12
    for directory in root.glob("decoder_type=*,*"):
        table = pq.read_table(directory / "swim_distance.parquet")
        values = table.column("swim_distance").to_numpy()
        assert values.shape == (2,)
        assert np.isfinite(values).all() and np.all(values >= 0)


@pytest.mark.parametrize("noise", ["bitflip", "depol", "uniform"])
def test_circuit_candidate_score_matches_ordinary_growth(noise):
    from color_code_stim import ColorCode
    from color_code_softoutput.circuit_level.decoder import CircuitLevelDecoder
    from color_code_softoutput.simulation.circuit_swim import CircuitCandidateSwim
    from color_code_softoutput.simulation.noise import make_noise_model

    code = ColorCode(d=3, rounds=3, circuit_type="tri",
                     cnot_schedule="tri_optimal",
                     noise_model=make_noise_model(noise, .01))
    detectors, _ = code.sample(8, seed=37)
    hard, candidates = code.decode(detectors, full_output=True,
                                   return_candidate_data=True)
    adapter_hard, growth = CircuitLevelDecoder(code).decode(detectors)
    np.testing.assert_array_equal(hard, adapter_hard)
    scores = CircuitCandidateSwim(code).score(detectors, hard, candidates)
    assert np.isfinite(scores).all()
    assert np.all(scores <= growth["selected_swim_distance"] + 1e-12)
