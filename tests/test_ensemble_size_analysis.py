"""Check ensemble parameters, unpooled references and plotted coordinates."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest
import numpy as np

from test_color_correlated_analysis import _run
from color_code_softoutput.analysis.ensemble_size import ensemble_size_table, plot_ensemble_size


def test_actual_parameter_and_reference_rates(tmp_path):
    run = _run(tmp_path, advanced=True, tesseract=True)
    table = ensemble_size_table(run, physical_error_rate=.01)
    assert len(table) == 6
    assert set(table.loc[table.curve == "perturbation", "ensemble_size"]) == {2}
    assert set(table.loc[table.curve == "baseline", "logical_error_rate"]) == {1 / 3}
    assert set(table.loc[table.curve == "tesseract", "logical_error_rate"]) == {0}
    fig, ax, plotted, legends = plot_ensemble_size(run, physical_error_rate=.01)
    # All observed ensemble and Tesseract rates are zero: no positive estimates.
    visible = [line for line in ax.lines if np.isfinite(line.get_ydata()).any()]
    assert len(visible) == 2
    assert all(line.get_linestyle() == ":" for line in visible)
    assert len(legends) == 2
    plt.close(fig)
    for figure, _ in legends.values():
        plt.close(figure)


def test_missing_reference_is_explicit(tmp_path):
    run = _run(tmp_path, advanced=True)
    with pytest.raises(ValueError, match="tesseract reference"):
        ensemble_size_table(run, physical_error_rate=.01)


def test_duplicate_sizes_do_not_merge_aliases(tmp_path):
    run = _run(tmp_path, alias_variants=True, tesseract=True)
    with pytest.raises(ValueError, match="options other than ensemble size differ"):
        ensemble_size_table(run, physical_error_rate=.01)
