"""Independent saved-file checks for selected cross-run comparisons."""

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.analysis.color_correlated import ColorCorrelatedRun
from color_code_softoutput.analysis.color_correlated_comparison import ColorCorrelatedComparison
from test_color_correlated_analysis import _run, _write_errors


@pytest.fixture
def sources(tmp_path):
    current, older = tmp_path / "current", tmp_path / "older"
    current.mkdir()
    older.mkdir()
    primary = _run(current, alias_variants=True)
    secondary = _run(older, tesseract=True)
    _write_errors(primary, "perturbation", [True, False, False],
                  baseline=[False, True, False], rescues=[0, 1, 0])
    _write_errors(secondary, "color_correlated", [True, False, False],
                  baseline=[False, True, True], rescues=[0, 1, 1])
    _write_errors(secondary, "tesseract", [True, False, False])
    return primary, secondary


def test_import_selected_decoder_and_prefer_primary_baseline(sources):
    primary, older = sources
    comparison = ColorCorrelatedComparison(primary, additional_sources=[{
        "run_directory": older.run_directory,
        "filter": {"decoder_type": ["tesseract", "color_correlated"]},
    }])
    assert comparison.run_directory == primary.run_directory
    assert len(comparison.catalog) == 16
    assert len(set(comparison.catalog.point_directory)) == 16
    assert len(comparison.source_manifest) == 2
    table = comparison.summary()
    assert set(table.source_run) == {str(primary.run_directory), str(older.run_directory)}
    ratio = comparison.improvement_table(physical_error_rate=.01)
    tesseract = ratio[ratio.decoder_alias == "tesseract"]
    assert set(tesseract.improvement_ratio) == {1.0}  # primary baseline, not older's 2.0
    assert set(tesseract.baseline_source_run) == {str(primary.run_directory)}
    assert set(tesseract.source_run) == {str(older.run_directory)}
    assert not tesseract.baseline_paired.any()
    own_older = ratio[ratio.decoder_alias == "color_correlated"]
    assert set(own_older.improvement_ratio) == {2.0}
    assert set(own_older.baseline_source_run) == {str(older.run_directory)}
    assert own_older.baseline_paired.all()
    # Selecting only the imported source still finds the primary baseline.
    selected = comparison.improvement_table(physical_error_rate=.01,
        filter={"decoder_alias": "tesseract", "source_run": str(older.run_directory)})
    assert set(selected.baseline_source_run) == {str(primary.run_directory)}
    for method in (comparison.count_table, comparison.better_weight_table, comparison.effect_table):
        selected = method({"decoder_alias": "tesseract"})
        assert len(selected) == 4
        assert set(selected.source_run) == {str(older.run_directory)}
    ler_fig, _, ler = comparison.plot_ler(baseline_compare=True)
    assert set(ler[ler.decoder_alias == "baseline"].source_run) == {str(primary.run_directory)}
    ratio_fig, _, _ = comparison.plot_improvement_ratio(physical_error_rate=.01)
    legends = comparison.plot_legends(ratio)
    for fig in (ler_fig, ratio_fig, *(item[0] for item in legends.values())):
        plt.close(fig)
    # Underlying single-run caches/catalogs keep relative identities untouched.
    assert all(not value.startswith("/") for value in primary.catalog.point_directory)
    assert all(not value.startswith("/") for value in primary.summary().point_directory)


def test_duplicate_points_require_filter_or_alias_map(sources):
    primary, _ = sources
    with pytest.raises(ValueError, match="Duplicate"):
        ColorCorrelatedComparison(primary, additional_sources=[{"run_directory": primary.run_directory}])
    with pytest.raises(ValueError, match="Duplicate saved point"):
        ColorCorrelatedComparison(primary, additional_sources=[{
            "run_directory": primary.run_directory, "filter": {"decoder_alias": "original_s2"},
            "alias_map": {"original_s2": "original_s2_reference"},
        }])
    _, older = sources
    clone_path = older.run_directory / "variants"
    clone_path.mkdir()
    clone = _run(clone_path, alias_variants=True)
    with pytest.raises(ValueError, match="Duplicate decoder_alias"):
        ColorCorrelatedComparison(primary, additional_sources=[{"run_directory": clone.run_directory}])
    mapped = ColorCorrelatedComparison(primary, additional_sources=[{
        "run_directory": clone.run_directory, "filter": {"decoder_alias": "original_s2"},
        "alias_map": {"original_s2": "original_s2_reference"},
    }])
    selected = mapped.summary({"decoder_alias": "original_s2_reference"})
    assert len(selected) == 4
    assert set(selected.source_run) == {str(clone.run_directory)}
    assert set(mapped.improvement_table(physical_error_rate=.01,
        filter={"decoder_alias": "original_s2_reference"}).baseline_source_decoder_alias) == {"original_s2_reference"}
    assert set(ColorCorrelatedRun(clone.run_directory).catalog.decoder_alias) == {"original_s2", "perturbed_s2"}


def test_incompatible_circuit_options_rejected(sources):
    primary, older = sources
    path = older.run_directory / "run_log.json"
    data = json.loads(path.read_text())
    data["config"]["color_code_options"] = {"perfect_logical_measurement": True}
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Incompatible physical"):
        ColorCorrelatedComparison(primary, additional_sources=[{
            "run_directory": older.run_directory, "filter": {"decoder_alias": "tesseract"}}])


def test_bad_source_or_alias_map_rejected(sources):
    primary, older = sources
    for source in ({}, {"run_directory": older.run_directory, "typo": True},
                   {"run_directory": older.run_directory, "filter": {"decoder_alias": "tesseract"},
                    "alias_map": {"unknown": "renamed"}}):
        with pytest.raises(ValueError):
            ColorCorrelatedComparison(primary, additional_sources=[source])


def test_different_shot_counts_keep_imported_denominator(sources):
    primary, older = sources
    path = older.run_directory / "run_log.json"
    data = json.loads(path.read_text())
    data["config"]["simulation"]["shots"] = 6
    path.write_text(json.dumps(data))
    for row in older.select({"decoder_alias": "tesseract"}).itertuples():
        pq.write_table(pa.table({"shot_index": pa.array(range(6), type=pa.int64()),
                               "logical_error": pa.array([True, False, True, False, True, False])}),
                       older.run_directory / row.point_directory / "logical_error.parquet")
    comparison = ColorCorrelatedComparison(primary, additional_sources=[{
        "run_directory": older.run_directory, "filter": {"decoder_alias": "tesseract"}}])
    table = comparison.improvement_table(physical_error_rate=.01,
                                        filter={"decoder_alias": "tesseract"})
    assert set(table.shots) == {6}
    assert set(table.failures) == {3}
    assert set(table.logical_error_rate) == {.5}
    np.testing.assert_allclose(table.improvement_ratio, 2/3)


def test_conflicting_alias_settings_on_disjoint_conditions_rejected(sources):
    primary, older = sources
    primary_log = primary.run_directory / "run_log.json"
    data = json.loads(primary_log.read_text())
    data["config"]["sweep"]["distance"] = 3
    primary_log.write_text(json.dumps(data))
    clone_path = older.run_directory / "variants"
    clone_path.mkdir()
    clone = _run(clone_path, alias_variants=True)
    clone_log = clone.run_directory / "run_log.json"
    data = json.loads(clone_log.read_text())
    data["config"]["sweep"]["distance"] = 5
    data["config"]["decoders"][0]["options"]["perturbation_ensemble_size"] = 16
    clone_log.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Different decoder settings"):
        ColorCorrelatedComparison(primary.run_directory, additional_sources=[{
            "run_directory": clone.run_directory,
            "filter": {"decoder_alias": "original_s2"}}])
