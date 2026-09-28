"""Ensemble-size ablations from saved runs, including external references."""

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from .color_correlated import PARAMETERS


def ensemble_size_table(run, *, physical_error_rate=0.03, filter=None,
                        reference_alias="tesseract"):
    """Return LER/Wilson rows with source provenance; never pool shots.

    Baseline is the existing API's deterministic representative ordinary
    decoder, not an average of independently sampled baselines. Import an
    older reference with ColorCorrelatedComparison when necessary.
    """
    selected = dict(filter or {})
    selected["physical_error_rate"] = physical_error_rate
    table = run._ler_table(selected, baseline_compare=True)
    ensemble = table.loc[table.decoder_type == "perturbation"].copy()
    if ensemble.empty:
        raise ValueError("No perturbation points selected")
    sizes, signatures = [], []
    for row in ensemble.itertuples():
        point = run._point_dirs[row.point_directory]
        options = dict(point.color_code_options) | dict(point.decoder_options)
        sizes.append(options.get("perturbation_ensemble_size", 1))
        signatures.append((tuple(sorted((k, repr(v)) for k, v in options.items()
                                        if k != "perturbation_ensemble_size")),
                           tuple(point.decode_options)))
    ensemble["ensemble_size"] = sizes
    if len(set(signatures)) != 1:
        raise ValueError("Perturbation options other than ensemble size differ; narrow filter")
    ensemble["curve"] = "perturbation"
    reference = table.loc[table.decoder_alias.isin(["baseline", reference_alias])].copy()
    reference["ensemble_size"] = np.nan
    reference["curve"] = reference.decoder_alias.map(
        {"baseline": "baseline", reference_alias: "tesseract"})
    result = pd.concat([ensemble, reference], ignore_index=True)
    # A line must not silently mix different physical experiments.
    for field in PARAMETERS:
        if field not in ("distance", "decoder_alias", "decoder_type", "rounds"):
            if result[field].nunique(dropna=False) != 1:
                raise ValueError(f"Multiple {field} values; narrow filter")
    if result.groupby("distance").rounds.nunique().max() > 1:
        raise ValueError("Multiple rounds per distance; narrow filter")
    if ensemble.duplicated(["distance", "ensemble_size"]).any():
        raise ValueError("Duplicate distance/ensemble_size; narrow filter")
    for distance in sorted(ensemble.distance.unique()):
        for curve in ("baseline", "tesseract"):
            if len(reference.loc[(reference.distance == distance) & (reference.curve == curve)]) != 1:
                raise ValueError(f"Need exactly one {curve} reference for distance={distance}")
    return result.sort_values(["distance", "curve", "ensemble_size"]).reset_index(drop=True)


def plot_ensemble_size(run, *, physical_error_rate=0.03, filter=None,
                       reference_alias="tesseract", plot_width=6.4,
                       plot_height=4.0, fontsize=11, ax=None):
    """Return (figure, axes, table, legends) with independent legend figures.

    Colors identify distance; solid circles show the ensemble, dotted lines
    the ordinary baseline, dashed lines Tesseract. Bands are 99% Wilson limits.
    Zero observations have bands only. The horizontal axis uses actual M,
    including the unperturbed baseline member; no interpolation is added.
    """
    table = ensemble_size_table(run, physical_error_rate=physical_error_rate,
                                filter=filter, reference_alias=reference_alias)
    if ax is None:
        figure, ax = plt.subplots(figsize=(plot_width, plot_height))
    else:
        figure = ax.figure
    distances = sorted(table.distance.unique())
    colors = dict(zip(distances, plt.rcParams["axes.prop_cycle"].by_key()["color"]))
    if len(colors) != len(distances):
        raise ValueError("Too many distances for the color cycle")
    lo, hi = table.ensemble_size.min(), table.ensemble_size.max()
    if lo == hi:
        lo, hi = lo - 0.5, hi + 0.5
    positive = table.loc[table.ler_low > 0, "ler_low"]
    floor = (float(positive.min()) if len(positive) == len(table)
             else min(float(table.ler_high.min()) / 10,
                      float(positive.min()) if len(positive) else np.inf)) / 1.5
    for (distance, curve), rows in table.groupby(["distance", "curve"]):
        rows = rows.sort_values("ensemble_size")
        color = colors[distance]
        if curve == "perturbation":
            x, y = rows.ensemble_size.to_numpy(), rows.logical_error_rate.to_numpy()
            # NaN breaks lines across zero observations on the logarithmic axis.
            ax.plot(x, np.where(y > 0, y, np.nan), "-o", color=color, markersize=4)
            lower, upper = rows.ler_low.to_numpy(), rows.ler_high.to_numpy()
        else:
            row = rows.iloc[0]
            x = np.array([lo, hi])
            if row.logical_error_rate > 0:
                ax.plot(x, [row.logical_error_rate] * 2, color=color,
                        linestyle=":" if curve == "baseline" else "--")
            lower, upper = np.repeat(row.ler_low, 2), np.repeat(row.ler_high, 2)
        ax.fill_between(x, np.maximum(lower, floor), upper, color=color, alpha=0.10)
    ax.set_yscale("log")
    ax.set_ylim(floor, min(1, table.ler_high.max() * 1.15))
    ax.set(xlabel="Ensemble size $M$", ylabel=("Logical error rate per round"
           if (table.noise_model == "uniform").all() else "Logical error rate"))
    ax.set_xticks(sorted(table.ensemble_size.dropna().unique()))
    ax.grid(True, alpha=0.25)
    legends = {}
    specifications = {
        "distance": ("Code distance", [Line2D([], [], color=colors[d], label=f"$d={d}$")
                                         for d in distances]),
        "decoder": ("Decoder", [Line2D([], [], color="black", linestyle=style, marker=marker,
                                  label=label) for style, marker, label in
                                  [("-", "o", "Perturbation"), (":", "", "Baseline"),
                                   ("--", "", "Tesseract")]]),
    }
    for name, (title, handles) in specifications.items():
        fig, axes = plt.subplots(figsize=(3 if name == "distance" else 4.5, 0.7))
        axes.axis("off")
        axes.legend(handles=handles, title=title, loc="center", ncol=len(handles),
                    fontsize=fontsize, title_fontsize=fontsize, frameon=False)
        legends[name] = (fig, axes)
    return figure, ax, table, legends
