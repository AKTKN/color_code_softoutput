"""Reusable orchestration for standard figures; no simulation logic."""
from pathlib import Path
import matplotlib.pyplot as plt
from .dataset import Phase2ADataset
from .prior_work import LeeFig3ReproductionAnalyzer
from .swim_distribution import SwimDistanceDistributionPlotter
from .conditional_ler import ConditionalLERAnalyzer
from .postselection import PostSelectionAnalyzer
from .selection import select_series
from .figure_style import RevtexFigureStyle


def standard_analysis(run_directory: Path, *, style: RevtexFigureStyle | None = None) -> dict:
    """Create standard prior-work, distribution, regression and paired retention outputs.

    Args:
        run_directory: Completed run directory.
        style: Defaults to publication TeX; test mode must be explicit.
    Returns:
        Prior-work crossing and fit tables.
    Notes:
        Fixed p=.04 when available and fixed d=7 when available. Analysis reads
        selected columns for one configuration at a time, not the full shot table.
    """
    dataset = Phase2ADataset(run_directory)
    style = style or RevtexFigureStyle()
    prior = LeeFig3ReproductionAnalyzer(style).analyze(dataset)
    values = dataset.available_values()
    fixed_p = .04 if .04 in values["physical_error_rate"] else values["physical_error_rate"][0]
    fixed_d = 7 if 7 in values["distance"] else values["distance"][0]
    selections = [(values["distance"],fixed_p),(fixed_d,values["physical_error_rate"])]
    for distance,probability in selections:
        for signed in (False,True):
            figure,_ = SwimDistanceDistributionPlotter(style).plot(dataset,distance=distance,
                physical_error_rate=probability,signed_logical_errors=signed)
            plt.close(figure)
        analyzer = ConditionalLERAnalyzer(style)
        figure,_,fits = analyzer.plot(dataset,distance=distance,physical_error_rate=probability)
        plt.close(figure)
        _,suffix = select_series(distance,probability)
        for figure in analyzer.plot_parameters(fits,output_directory=dataset.run_directory / "figures",suffix=suffix):
            plt.close(figure)
        figure,table = PostSelectionAnalyzer(style).plot(dataset,distance=distance,
            physical_error_rate=probability,include_forced_gap=True)
        plt.close(figure)
        if isinstance(distance,list):
            table.to_parquet(dataset.run_directory / "postselection.parquet",index=False)
    return prior
