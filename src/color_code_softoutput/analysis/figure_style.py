"""Context-scoped RevTeX typography, physical units and metric palettes."""
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import shutil
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from functools import lru_cache
import json
import subprocess
import sys


@lru_cache(maxsize=1)
def _rsmf_dimensions():
    # rsmf 0.2 constructs a formatter by changing the backend and global style.
    # Query its authoritative dimensions in an isolated process, once, so an
    # analysis call cannot close or alter preexisting notebook figures.
    program = ("import json,rsmf; "
               "f=rsmf.setup(r'\\documentclass[a4paper,reprint,unpublished]{revtex4-2}'); "
               "print(json.dumps([f.columnwidth,f.wide_columnwidth]))")
    return json.loads(subprocess.check_output([sys.executable,"-c",program],text=True))


def tex_pt_to_mpl_pt(tex_points: float) -> float:
    """Convert TeX 1/72.27-inch points to Matplotlib 1/72-inch points."""
    return tex_points * 72 / 72.27


def metric_palette(metric: str, count: int) -> list:
    """Return sequential YlGn (swim) or Blues (forced) shades, light to dark.

    Args:
        metric: 'selected_swim_distance' or 'forced_gap'.
        count: Positive number of interpolated colors, including counts above four.
    Raises:
        ValueError: Unknown metric or invalid count.
    """
    if metric not in ("selected_swim_distance", "forced_gap", "ordinary_path_gap", "comparative_path_gap", "ordinary_monotone_y_gap", "comparative_monotone_y_gap") or count < 1:
        raise ValueError("Known metric and positive palette length required")
    palette = plt.get_cmap("Blues" if metric == "forced_gap" else "YlGn")
    # Three-series plots use exactly .4, .7, .95 for d=3,5,7 in selection order.
    positions = np.interp(np.linspace(0, 2, count), [0, 1, 2], [.4, .7, .95])
    return [palette(float(x)) for x in positions]



@dataclass(frozen=True)
class RevtexFigureStyle:
    """Publication style with an explicit non-TeX mode for tests only.

    Args:
        test_mode: True disables TeX for CI; never an automatic fallback.
        base_tex_points: Manuscript font size in TeX points (default 10).
    Notes:
        Requires rsmf, latex, revtex4-2.cls, type1cm/type1ec and dvipng for PNG.
        Context restores all global rcParams even if plotting fails.
    """
    test_mode: bool = False
    base_tex_points: float = 10

    @contextmanager
    def context(self):
        """Yield scoped style; fail clearly if publication TeX tools are unavailable."""
        if not self.test_mode and any(shutil.which(tool) is None for tool in ("latex", "dvipng", "kpsewhich")):
            raise RuntimeError("Publication style requires LaTeX, revtex4-2 and dvipng; install TeX dependencies")
        with mpl.rc_context():
            size = tex_pt_to_mpl_pt(self.base_tex_points)
            mpl.rcParams.update({"font.size":size, "axes.labelsize":size*1.2, "axes.titlesize":size*1.2,
                "xtick.labelsize":size*1.2, "ytick.labelsize":size*1.2, "legend.fontsize":size*1.2,
                "xtick.direction":"in", "ytick.direction":"in", "xtick.top":True, "ytick.right":True,
                "axes.linewidth":tex_pt_to_mpl_pt(1), "lines.linewidth":tex_pt_to_mpl_pt(1),
                "lines.markersize":tex_pt_to_mpl_pt(4), "xtick.major.size":tex_pt_to_mpl_pt(3),
                "ytick.major.size":tex_pt_to_mpl_pt(3), "text.usetex":not self.test_mode, "font.family":"serif"})
            yield self

    def figure(self, *, wide: bool = True, aspect: float = .65):
        """Create (figure, axes) using rsmf column dimensions in inches.

        Args:
            wide: Use full two-column width if True, single column otherwise.
            aspect: Height divided by width; applies uniformly to plot families.
        Returns:
            Matplotlib Figure and Axes. Call inside context().
        """
        columnwidth, wide_columnwidth = _rsmf_dimensions()
        width = wide_columnwidth if wide else columnwidth
        return plt.subplots(figsize=(width, width*aspect), layout="constrained")


def save_figure(figure, directory: Path, stem: str) -> tuple[Path, Path]:
    """Save deterministic PDF and 160-dpi PNG paths; return both output paths."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = tuple(directory / f"{stem}.{extension}" for extension in ("pdf", "png"))
    for path in paths:
        figure.savefig(path, dpi=160)
    return paths
