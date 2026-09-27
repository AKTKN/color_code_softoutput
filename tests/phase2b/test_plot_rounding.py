"""Rounded score semantics and requested sequential colors, without sampling."""
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
import numpy as np
import pandas as pd
import pytest
from color_code_softoutput.analysis.statistics import grouped_rates, rounded_scores
from color_code_softoutput.analysis.postselection import postselection_curve, PostSelectionAnalyzer
from color_code_softoutput.analysis.swim_distribution import SwimDistanceDistributionPlotter
from color_code_softoutput.analysis.conditional_ler import ConditionalLERAnalyzer
from color_code_softoutput.analysis.figure_style import RevtexFigureStyle, metric_palette


@pytest.mark.parametrize('digits',[None,0,1,2,-1])
def test_round_actual_values_without_mutation(digits):
    values = np.array([2.675,1.25,1.35,15.1])
    before = values.copy()
    expected = before if digits is None else np.array([round(float(x),digits) for x in before])
    np.testing.assert_array_equal(rounded_scores(values,digits),expected)
    np.testing.assert_array_equal(values,before)
    assert not np.shares_memory(rounded_scores(values,digits),values)


@pytest.mark.parametrize('digits',[True,1.5,'2'])
def test_invalid_round_digits(digits):
    with pytest.raises(ValueError,match='round_digits'):
        grouped_rates([1,2],[False,True],round_digits=digits)
    with pytest.raises(ValueError,match='round_digits'):
        postselection_curve([1,2],[False,True],round_digits=digits)


def test_group_counts_and_postselection_whole_rounded_ties():
    scores = np.array([1.01,1.04,1.11,1.14,2.01])
    failures = np.array([True,False,True,False,True])
    table = grouped_rates(scores,failures,round_digits=1)
    np.testing.assert_allclose(table.score,[1,1.1,2])
    assert table.shots.tolist() == [2,2,1]
    assert table.failures.tolist() == [1,1,1]
    curve = postselection_curve(scores,failures,round_digits=1)
    assert curve.retained_shots.tolist() == [5,3,1]
    assert curve.retained_failures.tolist() == [3,2,1]
    pd.testing.assert_frame_equal(curve,postselection_curve(np.round(scores,1),failures))
    assert len(postselection_curve(scores,failures)) == 5
    # An explicit rounding request must not silently re-bin many rounded values.
    assert len(grouped_rates(np.arange(100)+.01,np.zeros(100),round_digits=0)) == 100


class Dataset:
    def __init__(self,directory):
        self.run_directory = directory
        self.scores = np.array([1.01,1.02,1.03,1.04])
    def metric_rows(self,metric,**kwargs):
        return pd.DataFrame({metric:self.scores.copy(),
            'ordinary_logical_error':[True,False,True,False],
            'comparative_logical_error':[False,False,True,False]})


def test_all_three_plot_apis_palette_markers_alpha_and_fit(tmp_path):
    dataset = Dataset(tmp_path)
    style = RevtexFigureStyle(test_mode=True)
    selection = dict(distance=[3,5,7],physical_error_rate=.003,round_digits=1)
    before = dataset.scores.copy()
    figure, counts = SwimDistanceDistributionPlotter(style).plot(dataset,**selection)
    try:
        np.testing.assert_array_equal(np.unique(counts.score),[1.])
        assert counts['count'].tolist() == [2,2]*3
        for j,collection in enumerate(figure.axes[0].collections):
            assert collection.get_alpha() == .75
            np.testing.assert_allclose(collection.get_facecolor()[0,:3],plt.get_cmap('YlGn')([.4,.7,.95][j//2])[:3])
            marker = MarkerStyle('o' if j%2==0 else 'x')
            expected = marker.get_path().transformed(marker.get_transform())
            np.testing.assert_array_equal(collection.get_paths()[0].vertices,expected.vertices)
    finally:
        plt.close(figure)
    figure,rates,fits = ConditionalLERAnalyzer(style).plot(dataset,**selection)
    try:
        assert rates.shots.tolist() == [4,4,4]
        assert rates.logical_error_rate.tolist() == [.5]*3
        assert fits.fit_status.tolist() == ['constant_score']*3
    finally:
        plt.close(figure)
    figure,curves = PostSelectionAnalyzer(style).plot(dataset,**selection,include_forced_gap=True)
    try:
        assert len(curves) == 6
        assert curves.retained_shots.tolist() == [4]*6
        assert curves.retained_failures.tolist() == [2]*3+[1]*3
        for j,line in enumerate(figure.axes[0].lines):
            expected = plt.get_cmap('YlGn' if j<3 else 'Blues')([.4,.7,.95][j%3])
            np.testing.assert_allclose(line.get_color(),expected)
    finally:
        plt.close(figure)
    np.testing.assert_array_equal(dataset.scores,before)
    assert len(list(tmp_path.rglob('*round1*.png'))) == 3
    assert list(tmp_path.glob('postselection_*round1*.parquet'))
