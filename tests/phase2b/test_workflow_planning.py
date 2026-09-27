"""Focused contract tests for the YAML workflow planning stage."""

from copy import deepcopy
from datetime import datetime

import pytest
import yaml

from color_code_softoutput.simulation.config import load_workflow_config, parse_workflow_config
from color_code_softoutput.simulation.noise import make_noise_model
from color_code_softoutput.simulation.planner import plan_points, point_directory_name, run_directory_name


@pytest.fixture
def raw():
    return {
        "simulation": {"output_root": "results", "shots": 100, "workers": 2,
                       "master_seed": 42, "buffer_shots": 50, "verbose": True},
        "chunking": {"calibration_shots": 8, "target_chunk_seconds": 1.0,
                     "min_chunk_shots": 1, "max_chunk_shots": 4096,
                     "throughput_ema_alpha": 0.25},
        "sweep": {"distance": 3, "physical_error_rate": 0.001, "noise_model": "uniform",
                  "rounds": "distance", "circuit_type": "tri", "cnot_schedule": "tri_optimal"},
        "color_code_options": {"temp_bdry_type": "Z"},
        "decoders": [{"type": "concat_mwpm", "options": {"comparative_decoding": False},
                      "decode_options": {"colors": "all"}}],
    }


def test_scalar_list_normalization(raw):
    config = parse_workflow_config(raw)
    assert config.sweep.distance == (3,)
    assert config.sweep.physical_error_rate == (0.001,)
    assert config.sweep.noise_model == ("uniform",)
    for key in ("distance", "physical_error_rate", "noise_model", "circuit_type", "cnot_schedule"):
        raw["sweep"][key] = [raw["sweep"][key]]
    assert parse_workflow_config(raw).hash8 == config.hash8


@pytest.mark.parametrize("section,key", [("simulation", "shots"), ("simulation", "verbose"),
                                         ("chunking", "min_chunk_shots"), ("sweep", "distance")])
def test_missing_required(raw, section, key):
    del raw[section][key]
    with pytest.raises(ValueError, match="Missing"):
        parse_workflow_config(raw)


@pytest.mark.parametrize("value", [-0.1, 1.1, True, "0.1", float("nan")])
def test_bad_probability(raw, value):
    raw["sweep"]["physical_error_rate"] = value
    with pytest.raises(ValueError, match="physical_error_rate"):
        parse_workflow_config(raw)


@pytest.mark.parametrize("key,value", [("distance", 2), ("distance", 4), ("rounds", 0),
                                           ("rounds", "d"), ("rounds", [1, -2])])
def test_bad_geometry(raw, key, value):
    raw["sweep"][key] = value
    with pytest.raises(ValueError):
        parse_workflow_config(raw)


def test_unknown_noise_and_unsafe_label(raw):
    raw["sweep"]["noise_model"] = "unknown"
    with pytest.raises(ValueError, match="Unknown noise"):
        parse_workflow_config(raw)
    raw["sweep"]["noise_model"] = "bitflip"
    for label in ("a/b", "a\\b", "a,b", "a=b"):
        raw["decoders"][0]["type"] = label
        with pytest.raises(ValueError, match="filesystem-safe"):
            parse_workflow_config(raw)


def test_cartesian_rounds_distance_and_ids(raw):
    raw["sweep"]["distance"] = [3, 5]
    raw["sweep"]["physical_error_rate"] = [0.001, 0.002]
    raw["sweep"]["noise_model"] = ["bitflip", "uniform"]
    raw["sweep"]["circuit_type"] = ["tri", "triangle"]
    raw["sweep"]["cnot_schedule"] = ["tri_optimal", "tri_optimal_reversed"]
    raw["decoders"].append({"type": "correlated", "options": {"enable_colorcorrelated_decoding": True}})
    config = parse_workflow_config(raw)
    points = plan_points(config)
    assert len(points) == 64
    assert {p.rounds for p in points if p.distance == 3} == {3}
    assert {p.rounds for p in points if p.distance == 5} == {5}
    assert len({p.point_id for p in points}) == 64
    assert [p.point_id for p in plan_points(config)] == [p.point_id for p in points]
    assert all(p.shots == 100 for p in points)


def test_explicit_rounds_product_and_name(raw):
    raw["sweep"]["rounds"] = [1, 3]
    points = plan_points(parse_workflow_config(raw))
    assert len(points) == 2
    assert point_directory_name(points[0]) == (
        "decoder_type=concat_mwpm,circuit_type=tri,d=3,r=1,p=0.001,"
        "noisemodel=uniform,cnot_schedule=tri_optimal")


def test_hash_yaml_order_comments_and_semantics(raw, tmp_path):
    a = tmp_path / "a.yml"
    b = tmp_path / "b.yml"
    a.write_text(yaml.safe_dump(raw), encoding="utf-8")
    b.write_text("# comment\n" + yaml.safe_dump(dict(reversed(list(raw.items())))), encoding="utf-8")
    config = load_workflow_config(a)
    assert load_workflow_config(b).hash8 == config.hash8
    assert len(config.hash8) == 8
    assert all(c in "0123456789abcdef" for c in config.hash8)
    changed = deepcopy(raw)
    changed["simulation"]["verbose"] = False
    assert parse_workflow_config(changed).hash8 != config.hash8
    assert run_directory_name(config, datetime(2026, 9, 27, 12, 34, 56)) == f"26_09_27_12_34_56_{config.hash8}"
    changed["simulation"]["output_root"] = "/another/machine/results"
    other = deepcopy(changed)
    other["simulation"]["output_root"] = "/this/machine/results"
    assert parse_workflow_config(changed).hash8 == parse_workflow_config(other).hash8


def test_path_collision_and_option_conflicts(raw):
    raw["sweep"]["physical_error_rate"] = [0.001, 0.001]
    with pytest.raises(ValueError, match="collision"):
        plan_points(parse_workflow_config(raw))
    raw["sweep"]["physical_error_rate"] = 0.001
    raw["decoders"][0]["options"]["rounds"] = 5
    with pytest.raises(ValueError, match="conflicts with sweep"):
        parse_workflow_config(raw)
    del raw["decoders"][0]["options"]["rounds"]
    raw["decoders"][0]["options"]["temp_bdry_type"] = "X"
    with pytest.raises(ValueError, match="Ambiguous"):
        parse_workflow_config(raw)


def test_formatted_probability_path_collision(raw):
    raw["sweep"]["physical_error_rate"] = [0.001, 0.0010000000000001]
    with pytest.raises(ValueError, match="collision"):
        plan_points(parse_workflow_config(raw))


def test_correlated_swim_capability(raw):
    raw["decoders"][0]["options"]["enable_colorcorrelated_decoding"] = True
    raw["decoders"][0]["decode_options"]["compute_swim_distance"] = True
    with pytest.raises(ValueError, match="cannot compute"):
        parse_workflow_config(raw)


def test_decoder_boolean_option_validation(raw):
    raw["decoders"][0]["options"]["comparative_decoding"] = "false"
    with pytest.raises(ValueError, match="must be boolean"):
        parse_workflow_config(raw)


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_verbose_boolean(raw, value):
    raw["simulation"]["verbose"] = value
    with pytest.raises(ValueError, match="verbose"):
        parse_workflow_config(raw)


def test_native_noise_parameters():
    p = 0.003
    bitflip = make_noise_model("bitflip", p)
    depol = make_noise_model("depol", p)
    uniform = make_noise_model("uniform", p)
    assert bitflip["bitflip"] == p and bitflip["depol"] == 0
    assert depol["depol"] == p and depol["bitflip"] == 0
    assert all(uniform[key] == p for key in ("reset", "meas", "cnot", "idle"))
    assert uniform["depol"] == uniform["bitflip"] == 0
    with pytest.raises(ValueError, match="Unknown"):
        make_noise_model("idle", p)
