"""Exact small-array accounting, ties and zero-reference behavior."""
import numpy as np
import pandas as pd
import pytest

from color_code_softoutput.analysis.dataset import METRIC_FAILURES
from color_code_softoutput.analysis.path_gap_comparison import compare_postselection


class Dataset:
    def __init__(self, directory, zero=False):
        self.run_directory = directory
        self.zero = zero

    def metric_rows(self, metric, **filters):
        scores = {'ordinary_path_gap': [3, 3, 3, 1],
                  'comparative_path_gap': [1, 2, 3, 4],
                  'forced_gap': [4, 3, 2, 1]}[metric]
        failures = ([False, False, False, False] if self.zero else
                    [True, False, True, False] if metric == 'ordinary_path_gap' else
                    [False, True, False, False])
        return pd.DataFrame(dict(config_id='test', batch_id=0, shot_index=np.arange(4),
                                 **{metric: scores, METRIC_FAILURES[metric]: failures}))


def test_counts_reduction_and_whole_ties(tmp_path):
    result = compare_postselection(Dataset(tmp_path), distance=3, physical_error_rate=.04,
                                  abort_rates=(0., .5))
    long = result['counts']
    matched = long[(long.policy == 'matched_abort') & (long.target_abort_rate == .5)]
    assert matched.retained_shots.tolist() == [2, 2, 2]
    assert matched.retained_failures.tolist() == [1, 0, 1]
    assert matched.reduction_rate.tolist() == [0., 1., -1.]
    whole = long[(long.policy == 'whole_ties') & (long.target_abort_rate == .5)]
    assert whole.retained_shots.tolist() == [3, 2, 2]
    assert whole.actual_abort_rate.tolist() == [.25, .5, .5]
    assert not whole.boundary_tie_split.any()
    assert result['report_path'].is_file()
    side = result['comparison'].query("policy == 'matched_abort' and target_abort_rate == .5").iloc[0]
    assert side.ordinary_path_gap_ler_ratio_to_forced == 1
    assert side.comparative_path_gap_ler_ratio_to_forced == 0
    assert side.comparative_path_gap_low_count_warning


def test_zero_failures_not_equivalence(tmp_path):
    result = compare_postselection(Dataset(tmp_path, zero=True), distance=3,
                                  physical_error_rate=.04, abort_rates=(0., .5))
    assert result['counts'].reduction_rate.isna().all()
    assert (result['counts'].ler_high > 0).all()
    assert result['comparison'].ordinary_path_gap_ler_ratio_to_forced.isna().all()
    assert result['comparison'].ordinary_path_gap_point_estimate_status.eq('undefined_zero_reference_failures').all()


@pytest.mark.parametrize('abort', [(-.1,), (1.,), (np.nan,), (.1, .1), ()])
def test_invalid_abort(tmp_path, abort):
    with pytest.raises(ValueError):
        compare_postselection(Dataset(tmp_path), distance=3, physical_error_rate=.04, abort_rates=abort)
