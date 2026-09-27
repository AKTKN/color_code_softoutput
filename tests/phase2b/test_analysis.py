import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from scipy.special import expit
from color_code_softoutput.analysis.figure_style import tex_pt_to_mpl_pt, metric_palette, RevtexFigureStyle
from color_code_softoutput.analysis.selection import select_series
from color_code_softoutput.analysis.swim_distribution import signed_scores, SwimDistanceDistributionPlotter
from color_code_softoutput.analysis.conditional_ler import ConditionalLERAnalyzer
from color_code_softoutput.analysis.statistics import grouped_rates, logistic_fit, wilson_interval
from color_code_softoutput.analysis.postselection import postselection_curve, PostSelectionAnalyzer
from color_code_softoutput.analysis.prior_work import crossing_estimate, scaling_fits
from color_code_softoutput.analysis.workflow import standard_analysis
from color_code_softoutput.analysis.dataset import Phase2ADataset
from color_code_softoutput.experiments.phase_2a_test import run_experiment
from color_code_softoutput.simulation.config import Phase2ATestConfig


def test_units_palette_and_context():
    assert tex_pt_to_mpl_pt(10) == pytest.approx(10*72/72.27)
    for n in [1,4,8]:
        for metric in ['forced_gap','selected_swim_distance']:
            assert len(metric_palette(metric,n)) == n
            assert metric_palette(metric,n) == metric_palette(metric,n)
    assert metric_palette('forced_gap',4)[0] != metric_palette('selected_swim_distance',4)[0]
    before = dict(mpl.rcParams)
    with RevtexFigureStyle(test_mode=True).context():
        assert not mpl.rcParams['text.usetex']
        figure, axes = RevtexFigureStyle(test_mode=True).figure()
        axes.plot([0,1],[0,1])
        plt.close(figure)
    assert dict(mpl.rcParams) == before


@pytest.mark.parametrize('distance,p,count',[(7,[.02,.04],2),([3,5],.04,2),(7,.04,1)])
def test_selection(distance,p,count):
    assert len(select_series(distance,p)[0]) == count


def test_both_sequences_rejected():
    with pytest.raises(ValueError,match='Only one'): select_series([3,5],[.02,.04])


def test_signed_and_binomial_counts():
    scores = np.array([1.,1.,2.,2.])
    failure = np.array([False,True,False,False])
    np.testing.assert_array_equal(signed_scores(scores,failure),[1,-1,2,2])
    np.testing.assert_array_equal(scores,[1,1,2,2])
    table = grouped_rates(scores,failure)
    assert table.shots.tolist() == [2,2]
    assert table.failures.tolist() == [1,0]
    assert table.logical_error_rate.tolist() == [.5,0]
    assert wilson_interval(0,10)[0] == 0
    assert wilson_interval(10,10)[1] == 1
    assert len(grouped_rates(scores,failure,bins=8)) == 2


def test_logistic_known_and_separation():
    rng = np.random.default_rng(2718)
    x = rng.uniform(0,5,30000)
    failures = rng.random(len(x)) > expit(.8*x-.4)
    fit = logistic_fit(x,failures)
    assert fit['fit_status'] == 'ok'
    assert fit['k'] == pytest.approx(.8,abs=.05)
    assert fit['l'] == pytest.approx(-.4,abs=.08)
    assert logistic_fit([1,2,3,4],[True,True,False,False])['fit_status'] == 'perfect_or_quasi_separation'
    assert logistic_fit(x,np.zeros(len(x),dtype=bool))['fit_status'] == 'single_outcome'


def test_exact_postselection():
    table = postselection_curve([4,3,2,1],[False,True,False,True])
    np.testing.assert_array_equal(table.threshold,[1,2,3,4])
    np.testing.assert_array_equal(table.retained_shots,[4,3,2,1])
    np.testing.assert_array_equal(table.retained_failures,[2,1,1,0])
    np.testing.assert_allclose(table.abort_rate,[0,.25,.5,.75])
    np.testing.assert_allclose(table.residual_logical_error_rate,[.5,1/3,.5,0])
    tied = postselection_curve([1,1,1],[True,False,False])
    assert tied.retained_failures.tolist() == [1]
    assert tied.retained_shots.tolist() == [3]
    assert tied.abort_rate.tolist() == [0]


def test_postselection_thresholds_keep_whole_ties():
    scores = np.array([2.,1.,3.,2.,1.,np.nextafter(2.,3.)])
    failures = np.array([True,False,True,False,True,False])
    table = postselection_curve(scores,failures)
    np.testing.assert_array_equal(table.threshold,np.unique(scores))
    for row in table.itertuples():
        retained = scores >= row.threshold
        assert row.retained_shots == retained.sum()
        assert row.retained_failures == failures[retained].sum()
        assert row.abort_rate == pytest.approx((~retained).mean())
        assert row.residual_logical_error_rate == failures[retained].mean()
        np.testing.assert_allclose([row.low,row.high],wilson_interval(
            failures[retained].sum(),retained.sum()))
    pd.testing.assert_frame_equal(table,postselection_curve(scores[::-1],failures[::-1]))


def test_postselection_plots_every_threshold_with_markers(tmp_path):
    class Dataset:
        run_directory = tmp_path

        def metric_rows(self, metric, **kwargs):
            return pd.DataFrame({metric: np.arange(1005),
                                 'ordinary_logical_error': True,
                                 'comparative_logical_error': True})

    figure,table = PostSelectionAnalyzer(RevtexFigureStyle(test_mode=True)).plot(
        Dataset(),distance=3,physical_error_rate=.04,include_forced_gap=True)
    try:
        assert len(figure.axes[0].lines) == 2
        for line,metric,style in zip(figure.axes[0].lines,
                ['selected_swim_distance','forced_gap'],['-','--']):
            curve = table[table.metric == metric]
            assert len(curve) == 1005
            np.testing.assert_allclose(line.get_xdata(),curve.abort_rate)
            np.testing.assert_allclose(line.get_ydata(),curve.residual_logical_error_rate)
            assert line.get_marker() == {'selected_swim_distance': 'D', 'forced_gap': 's'}[metric]
            assert line.get_linestyle() == style
    finally:
        plt.close(figure)


def test_crossing_and_scaling():
    rows = []
    for d in [3,5,7]:
        for p in [.076,.08,.084,.088]:
            rate = .08+(p-.083)*(d-5)
            rows.append(dict(distance=d,physical_error_rate=p,shots=1000000,ordinary_failures=rate*1000000))
    estimate = crossing_estimate(pd.DataFrame(rows))
    assert estimate['threshold'] == pytest.approx(.083,abs=1e-5)
    rows = []
    for d in [3,5,7]:
        for p in [.02,.03,.04,.05]:
            rows.append(dict(distance=d,physical_error_rate=p,shots=1e9,ordinary_failures=1e9*np.exp(.3*d)*p**(d*.5)))
    fits = scaling_fits(pd.DataFrame(rows))
    np.testing.assert_allclose(fits.G,[1.5,2.5,3.5])
    np.testing.assert_allclose(fits.C,[.9,1.5,2.1])
    rows[0]['ordinary_failures'] = 0
    assert scaling_fits(pd.DataFrame(rows)).iloc[0].points_excluded == 1
    rows[1]['ordinary_failures'] = 0
    assert scaling_fits(pd.DataFrame(rows)).iloc[0].fit_status == 'insufficient_nonzero_points'


def test_all_plot_families_and_metric_labels(tmp_path):
    config = Phase2ATestConfig(distances=(3,5,7),shots_per_point=16,batch_size=16,
                              num_workers=1,output_root=tmp_path,verbose=False)
    result = run_experiment(config)
    prior = standard_analysis(result.run_directory,style=RevtexFigureStyle(test_mode=True))
    assert (result.run_directory/'PRIOR_WORK_REPRODUCTION.md').exists()
    assert len(list((result.run_directory/'figures').glob('*.pdf'))) >= 16
    dataset = Phase2ADataset(result.run_directory)
    distribution, _ = SwimDistanceDistributionPlotter(RevtexFigureStyle(test_mode=True)).plot(
        dataset, distance=3, physical_error_rate=.04
    )
    assert distribution.axes[0].get_yscale() == "log"
    plt.close(distribution)
    conditional, empirical_rates, _ = ConditionalLERAnalyzer(RevtexFigureStyle(test_mode=True)).plot(
        dataset, distance=3, physical_error_rate=.04
    )
    assert conditional.axes[0].get_yscale() == "log"
    assert set(empirical_rates) >= {"logical_error_rate", "low", "high"}
    plt.close(conditional)
    figure,table = PostSelectionAnalyzer(RevtexFigureStyle(test_mode=True)).plot(dataset,distance=3,physical_error_rate=.04,include_forced_gap=True)
    assert figure.axes[0].get_yscale() == "log"
    for metric,failure in [('selected_swim_distance','ordinary_logical_error'),('forced_gap','comparative_logical_error')]:
        rows = dataset.metric_rows(metric,distance=3,physical_error_rate=.04)
        curve = table[table.metric == metric]
        assert curve.iloc[0].retained_failures == rows[failure].sum()
        assert set(curve.failure_column) == {failure}
    plt.close(figure)


def test_distribution_forced_overlay_counts_and_labels(tmp_path):
    class Dataset:
        run_directory = tmp_path
        score_label = "Path gap"

        def metric_rows(self, metric, **selection):
            return pd.DataFrame({
                "ordinary_path_gap": [-1., -1., 2., 2.],
                "forced_gap": [3., 3. + 1e-15, 9., 9.],
                "ordinary_logical_error": [True, False, False, False],
                "comparative_logical_error": [False, False, True, True],
            })

    plotter = SwimDistanceDistributionPlotter(RevtexFigureStyle(test_mode=True))
    figure, table = plotter.plot(Dataset(), distance=5, physical_error_rate=.04,
                                metric="ordinary_path_gap", include_forced_gap=True,
                                normalize_frequency=True)
    try:
        assert set(table.metric) == {"ordinary_path_gap", "forced_gap"}
        for metric, failure, errors in (("ordinary_path_gap", "ordinary_logical_error", 1),
                                        ("forced_gap", "comparative_logical_error", 2)):
            rows = table[table.metric == metric]
            assert rows["count"].sum() == 4
            assert rows.frequency.sum() == pytest.approx(1)
            assert rows.loc[rows.logical_error, "count"].sum() == errors
            assert set(rows.failure_column) == {failure}
        assert table.loc[table.metric == "forced_gap", "score"].nunique() == 2
        assert figure.axes[0].get_xlabel() == "Soft-output score"
        assert list((tmp_path / "figures").glob('*_with_forced_gap.png'))
    finally:
        plt.close(figure)
    figure, table = plotter.plot(Dataset(), distance=5, physical_error_rate=.04,
                                metric="forced_gap", include_forced_gap=True)
    try:
        assert table["count"].sum() == 4  # no duplicate forced-gap overlay
        assert figure.axes[0].get_xlabel() == "Forced gap"
    finally:
        plt.close(figure)
