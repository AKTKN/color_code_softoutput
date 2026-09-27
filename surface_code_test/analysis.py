"""Surface data adapter and shared-style distribution/conditional/retention plots."""
from pathlib import Path
import json
from matplotlib import colormaps
from tempfile import TemporaryDirectory
import numpy as np
import pandas as pd
from color_code_softoutput.analysis.dataset import Phase2ADataset
from color_code_softoutput.analysis.swim_distribution import SwimDistanceDistributionPlotter
from color_code_softoutput.analysis.conditional_ler import ConditionalLERAnalyzer
from color_code_softoutput.analysis.postselection import postselection_curve
from color_code_softoutput.analysis.selection import select_series
from color_code_softoutput.analysis.figure_style import RevtexFigureStyle, metric_palette, save_figure
from .simulation import SHOT_SCHEMA, LEGACY_SHOT_SCHEMA
from .model import PATH_GAP_VERSION


class SurfaceDataset(Phase2ADataset):
    """Load strict surface shards and adapt names for the shared plot classes.

    Args:
        run_directory: Surface run with metadata.json and shots/*.parquet.
        units: 'natural' or 'dB'; conversion 10/log(10) is display-only, no rounding.
    Raises: ValueError for wrong experiment, schema, config hash or units.
    Notes: All scores use ordinary_logical_error on the same saved physical shots.
    """
    def __init__(self, run_directory: Path, *, units: str = 'dB'):
        metadata = json.loads((Path(run_directory)/'metadata.json').read_text())
        version = metadata.get('path_gap_metric_version')
        if version not in (None, PATH_GAP_VERSION):
            raise ValueError('Unknown path-gap metric version')
        self.has_path_gap = version is not None
        super().__init__(run_directory,shot_schema=SHOT_SCHEMA if self.has_path_gap else LEGACY_SHOT_SCHEMA)
        if self.metadata.get('experiment_name') != 'surface_code_memory':
            raise ValueError('Expected surface-code memory run')
        if units not in ('natural','dB'):
            raise ValueError('units must be natural or dB')
        self.units = units
        self.scale = 10/np.log(10) if units == 'dB' else 1.

    def metric_rows(self, metric: str, *, distance=None, physical_error_rate=None, failure_column=None) -> pd.DataFrame:
        """Return display-scaled metric rows; aliases are only for plot compatibility.

        Args: metric: swim_distance/complementary_gap/path_gap or shared plot alias.
        Returns: Rows sorted by shot ID with ordinary failure labels. The legacy
            forced_gap alias maps to complementary_gap with the same ordinary label.
        Raises: ValueError for any unsupported metric/failure association.
        """
        names = {'selected_swim_distance':'swim_distance','forced_gap':'complementary_gap',
                 'swim_distance':'swim_distance','complementary_gap':'complementary_gap',
                 'ordinary_path_gap':'path_gap','path_gap':'path_gap'}
        if metric not in names or failure_column not in (None,'ordinary_logical_error'):
            raise ValueError('Surface scores use ordinary failures')
        name = names[metric]
        if name == 'path_gap' and not self.has_path_gap:
            raise ValueError('This legacy run has no path-gap samples; use a new run')
        rows = self.read(['config_id','batch_id','shot_index','distance','physical_error_rate',name,'ordinary_logical_error'],
                         distance=distance,physical_error_rate=physical_error_rate)
        rows = rows.rename(columns={name:metric})
        rows[metric] *= self.scale
        return rows.sort_values(['config_id','batch_id','shot_index'])


def plot_distribution(dataset: SurfaceDataset, *, metric="swim_distance", style: RevtexFigureStyle | None = None):
    """Save shared outcome-marked swim or path-gap distribution PDF/PNG and counts; return both.

    Units follow dataset.units; bins are display bins and do not change saved shots.
    """
    style = style or RevtexFigureStyle()
    if metric not in ('swim_distance','path_gap'):
        raise ValueError('Expected swim_distance or path_gap')
    alias = 'ordinary_path_gap' if metric == 'path_gap' else 'selected_swim_distance'
    label = 'Path gap v1' if metric == 'path_gap' else 'Swim distance'
    values = dataset.available_values()
    with TemporaryDirectory(prefix='surface-plot-') as temporary:
        figure, table = SwimDistanceDistributionPlotter(style).plot(dataset,distance=values['distance'],
            physical_error_rate=values['physical_error_rate'][0],metric=alias,output_directory=Path(temporary))
    with style.context():
        figure.axes[0].set_xlabel(label+' ('+dataset.units+')')
        save_figure(figure,dataset.run_directory/'figures','surface_'+('path_gap' if metric == 'path_gap' else 'swim')+'_distribution_'+dataset.units)
    table.to_parquet(dataset.run_directory/f'{"path_gap_" if metric == "path_gap" else ""}distribution_{dataset.units}.parquet',index=False)
    return figure,table


def plot_conditional_ler(dataset: SurfaceDataset, *, metric="swim_distance", style: RevtexFigureStyle | None = None):
    """Save conditional LER with Wilson intervals and counts, without a fitted curve.

    Returns: (figure, empirical table, fit diagnostics) from shared analysis.
    Fits are exploratory diagnostics only; no confidence calibration is asserted.
    """
    style = style or RevtexFigureStyle()
    if metric not in ('swim_distance','path_gap'):
        raise ValueError('Expected swim_distance or path_gap')
    alias = 'ordinary_path_gap' if metric == 'path_gap' else 'selected_swim_distance'
    label = 'Path gap v1' if metric == 'path_gap' else 'Swim distance'
    values = dataset.available_values()
    with TemporaryDirectory(prefix='surface-plot-') as temporary:
        figure,table,fits = ConditionalLERAnalyzer(style).plot(dataset,distance=values['distance'],
            physical_error_rate=values['physical_error_rate'][0],metric=alias,overlay_fit=False,output_directory=Path(temporary))
    with style.context():
        figure.axes[0].set_xlabel(label+' ('+dataset.units+')')
        zero_distances = [int(d) for d,part in table.groupby('distance') if part.failures.sum()==0]
        if zero_distances:
            figure.axes[0].text(.98,.04,'No observed failures: d='+','.join(map(str,zero_distances)),
                                ha='right',transform=figure.axes[0].transAxes,fontsize=8)
        save_figure(figure,dataset.run_directory/'figures','surface_'+('path_gap_' if metric == 'path_gap' else '')+'conditional_ler_'+dataset.units)
    table.to_parquet(dataset.run_directory/f'{"path_gap_" if metric == "path_gap" else ""}conditional_ler_{dataset.units}.parquet',index=False)
    return figure,table,fits


def plot_postselection(dataset: SurfaceDataset, *, style: RevtexFigureStyle | None = None):
    """Save paired swim/complementary/path-gap retention curves, exact thresholds and ties.

    Returns: Figure and table including all zero-failure rows and Wilson intervals.
    All scores retain >= threshold, use ordinary failures, and include no-abort.
    Zero empirical rates are stored but omitted on the logarithmic plot.
    """
    style = style or RevtexFigureStyle()
    values = dataset.available_values()
    series,_ = select_series(values['distance'],values['physical_error_rate'][0])
    tables = []
    with style.context():
        figure,axes = style.figure()
        metrics = [
            ('swim_distance','selected_swim_distance','swim','-'),
            ('complementary_gap','forced_gap','complementary gap','--')]
        if dataset.has_path_gap:
            metrics.append(('path_gap','ordinary_path_gap','path gap v1',':'))
        for metric,alias,label,linestyle in metrics:
            colors = (list(colormaps['Purples'](np.linspace(.45,.95,len(series))))
                      if metric == 'path_gap' else metric_palette(alias,len(series)))
            for item,color in zip(series,colors):
                # Sort/group on original scores, before any display-unit conversion.
                rows = dataset.read([metric,'ordinary_logical_error'],distance=item.distance,
                                    physical_error_rate=item.physical_error_rate)
                table = postselection_curve(rows[metric],rows.ordinary_logical_error)
                table['threshold_natural'] = table.threshold
                table['threshold'] *= dataset.scale
                table['units'] = dataset.units
                table['metric'] = metric
                table['failure_column'] = 'ordinary_logical_error'
                table['distance'] = item.distance
                table['physical_error_rate'] = item.physical_error_rate
                tables.append(table)
                keep = table.residual_logical_error_rate > 0
                axes.plot(table.abort_rate[keep],table.residual_logical_error_rate[keep],color=color,
                          marker='o',linestyle=linestyle,label=f'{item.label}, {label}')
        positive = any((t.residual_logical_error_rate>0).any() for t in tables)
        if not positive:
            axes.set_ylim(max(1e-8,.5/max(t.retained_shots.max() for t in tables)),1)
        zero_distances = [int(t.distance.iloc[0]) for t in tables
                          if t.metric.iloc[0]=='swim_distance' and t.retained_failures.max()==0]
        if zero_distances:
            axes.text(.98,.04,'No observed failures: d='+','.join(map(str,zero_distances)),
                      ha='right',transform=axes.transAxes,fontsize=8)
        axes.set(xlabel='Abort rate',ylabel='Residual logical error rate',xlim=(0,1),yscale='log')
        figure.legend(ncol=2,loc='outside upper center')
        save_figure(figure,dataset.run_directory/'figures','surface_postselection_'+dataset.units)
    table = pd.concat(tables,ignore_index=True)
    table.to_parquet(dataset.run_directory/f'postselection_{dataset.units}.parquet',index=False)
    return figure,table


def standard_analysis(dataset: SurfaceDataset, *, style: RevtexFigureStyle | None = None) -> None:
    """Save all three plot families and tables and close each Matplotlib figure."""
    import matplotlib.pyplot as plt
    for function in (plot_distribution,plot_conditional_ler,plot_postselection):
        outputs = function(dataset,style=style)
        plt.close(outputs[0])
    if dataset.has_path_gap:
        for function in (plot_distribution,plot_conditional_ler):
            outputs = function(dataset,metric='path_gap',style=style)
            plt.close(outputs[0])

