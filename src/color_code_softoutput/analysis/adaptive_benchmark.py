"""Validated same-shot summaries for adaptive_v2 benchmark results."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ..simulation.adaptive_benchmark import KINDS, _TYPES, read_weights
from .statistics import wilson_interval


def _read_metric(root: Path, name: str, shots: int) -> np.ndarray:
    table = pq.read_table(root / f"{name}.parquet")
    schema = pa.schema([pa.field("shot_index", pa.int64(), nullable=False),
                        pa.field(name, _TYPES[name], nullable=False)])
    if table.schema != schema or len(table) != shots or any(col.null_count for col in table.columns):
        raise ValueError(f"invalid metric sidecar: {name}")
    if not np.array_equal(table.column("shot_index").to_numpy(), np.arange(shots)):
        raise ValueError(f"invalid shot identities: {name}")
    return table.column(name).to_numpy()


class AdaptiveBenchmarkRun:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory).expanduser().resolve()
        manifest = json.loads((self.directory / "manifest.json").read_text())
        if manifest.get("schema_version") != "adaptive_v2" or (self.directory / "FAILED").exists():
            raise ValueError("incomplete or incompatible adaptive benchmark")
        self.manifest = manifest
        shots = manifest["shots"]
        self.metrics = {name: _read_metric(self.directory, name, shots) for name in _TYPES}
        self.weights = {name: read_weights(self.directory / f"{name}_candidate_weights.parquet")
                        for name in ("color_correlated", "relift", "perturbation")}
        for name, (_, basis, _) in self.weights.items():
            if basis != manifest["candidate_weight_basis"]:
                raise ValueError(f"{name} candidate weight basis differs from manifest")
        for name in ("color_correlated_run", "relift_run"):
            if np.any(self.metrics[name] > 2):
                raise ValueError(f"invalid {name} class")
        if not np.array_equal(self.metrics["color_correlated_run"], self.metrics["relift_run"]):
            raise ValueError("paired baseline run classes disagree")
        if np.any(self.metrics["relift_candidate_slots"] != 12):
            raise ValueError("relift logical candidate slots differ from 12")
        if not np.array_equal(self.metrics["relift_unique_stage2_syndromes"],
                              3 + self.metrics["relift_extra_stage2_calls"]):
            raise ValueError("unique Stage-2 problems disagree with executed calls")

    def by_class(self, strategy: str) -> pd.DataFrame:
        if strategy not in ("relift", "color_correlated"):
            raise ValueError("strategy must be relift or color_correlated")
        m = self.metrics
        labels = m["relift_run" if strategy == "relift" else "color_correlated_run"]
        baseline = m["baseline_error"]
        errors = m[f"{strategy}_error"]
        rows = []
        for category in range(3):
            mask = labels == category
            count = int(mask.sum())
            row = {"run_class": category, "shots": count,
                   "shot_fraction": count / len(labels),
                   "ler": float(np.mean(errors[mask])) if count else np.nan,
                   "rescue_rate": float(np.mean(baseline[mask] & ~errors[mask])) if count else np.nan,
                   "regression_rate": float(np.mean(~baseline[mask] & errors[mask])) if count else np.nan}
            call_key = ("relift_extra_stage2_calls" if strategy == "relift"
                        else "color_correlated_extra_mwpm_calls")
            calls = m[call_key][mask]
            row.update(mean_extra_mwpm_calls=float(np.mean(calls)) if count else np.nan,
                       median_extra_mwpm_calls=float(np.median(calls)) if count else np.nan)
            if strategy == "relift":
                kinds = m["relift_selected_kind"][mask]
                row.update({f"selected_{kind}_fraction": float(np.mean(kinds == index)) if count else np.nan
                            for index, kind in enumerate(KINDS)})
                row["selected_advanced_fraction"] = float(np.mean(kinds > 0)) if count else np.nan
            else:
                kinds = m["color_correlated_selected_kind"][mask]
                row.update({f"selected_{kind}_fraction": float(np.mean(kinds == index)) if count else np.nan
                            for index, kind in enumerate(("baseline", "guided"))})
                row["selected_advanced_fraction"] = float(np.mean(kinds > 0)) if count else np.nan
            rows.append(row)
        return pd.DataFrame(rows)

    def overall_relift(self) -> dict:
        m = self.metrics
        shots = self.manifest["shots"]
        proposed = int(np.sum(m["relift_cache_skips"] + m["relift_extra_stage2_calls"]))
        solved = m["relift_unique_stage2_syndromes"]
        unique, counts = np.unique(solved, return_counts=True)
        return {
            "pairwise_baseline_syndrome_equal_fraction": float(np.sum(m["relift_pairwise_baseline_equal"]) / (6 * shots)),
            "same_target_cache_skip_fraction": float(np.sum(m["relift_cache_skips"]) / proposed) if proposed else np.nan,
            "unique_stage2_problems_per_shot": dict(zip(map(int, unique), map(int, counts))),
            "same_target_duplicate_syndromes_per_shot": float(np.mean(m["relift_cache_skips"])),
            "unique_extra_relift_solves_per_shot": float(np.mean(m["relift_extra_stage2_calls"])),
            "all_color_new_syndrome_fraction": float(np.sum(m["relift_all_color_new"]) / (3 * shots)),
        }

    def point_summary(self) -> pd.DataFrame:
        """One row per strategy, including observed work and paired outcomes."""
        m, manifest = self.metrics, self.manifest
        baseline = m["baseline_error"]
        rows = []
        for strategy in ("baseline", "color_correlated", "relift", "perturbation"):
            errors = m[f"{strategy}_error"]
            shots = len(errors)
            low, high = wilson_interval(int(np.count_nonzero(errors)), shots)
            calls = (np.full(shots, 6) if strategy == "baseline" else
                6 + m["color_correlated_extra_mwpm_calls"] if strategy == "color_correlated" else
                m["relift_total_mwpm_calls"] if strategy == "relift" else
                np.full(shots, 6 * manifest["ensemble_size"]))
            row = dict(strategy=strategy, distance=manifest["distance"],
                physical_error_rate=manifest["physical_error_rate"],
                weight_basis=manifest["candidate_weight_basis"], shots=shots,
                ler=float(np.mean(errors)), wilson_low=float(low), wilson_high=float(high),
                rescue_rate=float(np.mean(baseline & ~errors)),
                regression_rate=float(np.mean(~baseline & errors)),
                nominal_max_mwpm_calls=manifest["nominal_max_mwpm_calls"][strategy],
                mean_actual_mwpm_calls=float(np.mean(calls)),
                median_actual_mwpm_calls=float(np.median(calls)),
                p90_actual_mwpm_calls=float(np.quantile(calls, .9)),
                p99_actual_mwpm_calls=float(np.quantile(calls, .99)),
                decode_seconds=manifest["decode_seconds"][strategy],
                seconds_per_shot=manifest["decode_seconds"][strategy] / shots,
                ensemble_size=manifest["ensemble_size"] if strategy == "perturbation" else np.nan,
                alpha=manifest["alpha"] if strategy == "perturbation" else np.nan)
            if strategy == "relift":
                row.update({f"selected_{kind}_fraction": float(np.mean(m["relift_selected_kind"] == i))
                    for i, kind in enumerate(KINDS)})
            elif strategy == "color_correlated":
                row["selected_advanced_fraction"] = float(np.mean(m["color_correlated_selected_kind"] == 1))
            elif strategy == "perturbation":
                row.update(mean_unique_stage1=float(np.mean(m["perturbation_unique_stage1"])),
                    mean_unique_final_corrections=float(np.mean(m["perturbation_unique_corrections"])),
                    duplicate_member_fraction=float(np.mean(m["perturbation_duplicate_member_fraction"])))
                row.update({f"selected_member_{member}_fraction": float(np.mean(
                    m["perturbation_selected_member"] == member))
                    for member in range(manifest["ensemble_size"])})
            rows.append(row)
        return pd.DataFrame(rows)

    def class_summary(self) -> pd.DataFrame:
        frames = []
        for strategy in ("color_correlated", "relift"):
            frame = self.by_class(strategy)
            frame.insert(0, "strategy", strategy)
            frame.insert(1, "distance", self.manifest["distance"])
            frame.insert(2, "physical_error_rate", self.manifest["physical_error_rate"])
            frame.insert(3, "weight_basis", self.manifest["candidate_weight_basis"])
            frames.append(frame)
        return pd.concat(frames, ignore_index=True)

    def call_distribution(self) -> pd.DataFrame:
        m = self.metrics
        shots = self.manifest["shots"]
        vectors = {"baseline": np.full(shots, 6),
            "color_correlated": 6 + m["color_correlated_extra_mwpm_calls"],
            "relift": m["relift_total_mwpm_calls"],
            "perturbation": np.full(shots, 6 * self.manifest["ensemble_size"])}
        return pd.DataFrame({"strategy": strategy, "calls": int(value),
            "shots": int(count), "weight_basis": self.manifest["candidate_weight_basis"]}
            for strategy, vector in vectors.items()
            for value, count in zip(*np.unique(vector, return_counts=True)))


def collect_runs(directories) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    runs = [AdaptiveBenchmarkRun(path) for path in directories]
    if not runs:
        raise ValueError("no benchmark runs")
    points = pd.concat([run.point_summary() for run in runs], ignore_index=True)
    classes = pd.concat([run.class_summary() for run in runs], ignore_index=True)
    calls = pd.concat([run.call_distribution() for run in runs], ignore_index=True)
    early = pd.DataFrame([dict(run.overall_relift(),
        distance=run.manifest["distance"], physical_error_rate=run.manifest["physical_error_rate"],
        weight_basis=run.manifest["candidate_weight_basis"]) for run in runs])
    return points, classes, calls, early


def save_report(directories, output_directory: str | Path) -> None:
    """Save basis-labelled tables and the required diagnostic plot families."""
    import matplotlib.pyplot as plt

    paths = list(directories)
    points, classes, calls, early = collect_runs(paths)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    for name, table in (("points", points), ("run_classes", classes),
                        ("call_distribution", calls), ("relift_early_exit", early)):
        table.to_csv(output / f"{name}.csv", index=False)
    perturbation = points[points.strategy == "perturbation"].sort_values(
        ["weight_basis", "distance", "physical_error_rate", "alpha", "ensemble_size"]).copy()
    perturbation["ler_change_from_previous_m"] = perturbation.groupby(
        ["weight_basis", "distance", "physical_error_rate", "alpha"]).ler.diff()
    perturbation["unique_correction_change_from_previous_m"] = perturbation.groupby(
        ["weight_basis", "distance", "physical_error_rate", "alpha"]).mean_unique_final_corrections.diff()
    perturbation.to_csv(output / "perturbation_saturation.csv", index=False)
    selected = []
    for path in paths:
        run = AdaptiveBenchmarkRun(path)
        values = run.metrics["perturbation_selected_member"]
        for member, count in zip(*np.unique(values, return_counts=True)):
            selected.append(dict(distance=run.manifest["distance"],
                physical_error_rate=run.manifest["physical_error_rate"],
                weight_basis=run.manifest["candidate_weight_basis"],
                ensemble_size=run.manifest["ensemble_size"], alpha=run.manifest["alpha"],
                member=int(member), fraction=int(count) / len(values)))
    pd.DataFrame(selected).to_csv(output / "perturbation_selected_members.csv", index=False)
    for basis in sorted(points.weight_basis.unique()):
        p = points[points.weight_basis == basis]
        c = classes[classes.weight_basis == basis]
        e = early[early.weight_basis == basis]
        suffix = basis

        def figure(filename, xlabel, ylabel, series, xlog=False):
            fig, ax = plt.subplots(figsize=(6, 4))
            for label, x, y in series:
                ax.plot(x, y, marker="o", label=label)
            ax.set(xlabel=xlabel, ylabel=ylabel, title=f"Weight basis: {basis}")
            if xlog:
                ax.set_xscale("log")
            ax.grid(alpha=.25)
            if len(series) > 1:
                ax.legend(fontsize=8)
            fig.tight_layout()
            fig.savefig(output / f"{filename}_{suffix}.png", dpi=160)
            plt.close(fig)

        # Show a fixed perturbation setting alongside all three other strategies.
        fixed = p[(p.strategy != "perturbation") |
                  ((p.ensemble_size == 2) & (p.alpha == .25))]
        for xcol, filename, xlabel in (("physical_error_rate", "ler_vs_p", "Physical error rate"),
                                      ("mean_actual_mwpm_calls", "ler_vs_calls", "Mean actual MWPM calls"),
                                      ("seconds_per_shot", "ler_vs_runtime", "Decode seconds per shot")):
            series = []
            for (strategy, distance), frame in fixed.groupby(["strategy", "distance"]):
                frame = frame.sort_values(xcol)
                series.append((f"{strategy}, d={distance}", frame[xcol], frame.ler))
            figure(filename, xlabel, "LER", series, xlog=xcol == "physical_error_rate")

        for xcol, filename in (("distance", "class_fraction_vs_distance"),
                               ("physical_error_rate", "class_fraction_vs_p")):
            series = []
            for (strategy, category), frame in c.groupby(["strategy", "run_class"]):
                frame = frame.groupby(xcol, as_index=False).shot_fraction.mean().sort_values(xcol)
                series.append((f"{strategy} class {category}", frame[xcol], frame.shot_fraction))
            figure(filename, xcol, "Shot fraction", series)

        fig, ax = plt.subplots(figsize=(6, 4))
        call_data = calls[calls.weight_basis == basis].groupby(["strategy", "calls"], as_index=False).shots.sum()
        for strategy, frame in call_data.groupby("strategy"):
            ax.plot(frame.calls, frame.shots / frame.shots.sum(), marker="o", label=strategy)
        ax.set(xlabel="Actual MWPM calls", ylabel="Shot fraction", title=f"Weight basis: {basis}")
        ax.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(output / f"actual_call_distribution_{suffix}.png", dpi=160); plt.close(fig)

        series = []
        for strategy, frame in c.groupby("strategy"):
            frame = frame.groupby("run_class", as_index=False)[["rescue_rate", "regression_rate"]].mean()
            for metric in ("rescue_rate", "regression_rate"):
                series.append((f"{strategy} {metric}", frame.run_class, frame[metric]))
        figure("rescue_regression_by_class", "Run class", "Paired fraction", series)
        figure("relift_early_exit", "Physical error rate", "Pairwise baseline syndrome equality fraction",
               [(f"d={d}", frame.physical_error_rate,
                 frame.pairwise_baseline_syndrome_equal_fraction)
                for d, frame in e.groupby("distance")])
        kind_cols = [f"selected_{kind}_fraction" for kind in KINDS]
        rel = p[p.strategy == "relift"].groupby("physical_error_rate", as_index=False)[kind_cols].mean()
        figure("relift_selected_kind", "Physical error rate", "Selected fraction",
               [(kind, rel.physical_error_rate, rel[f"selected_{kind}_fraction"]) for kind in KINDS])
        perturb = p[p.strategy == "perturbation"]
        figure("perturbation_vs_m_alpha", "Ensemble size M", "LER",
               [(f"d={distance}, p={rate:g}, alpha={alpha}", frame.ensemble_size, frame.ler)
                for (distance, rate, alpha), frame in perturb.groupby(
                    ["distance", "physical_error_rate", "alpha"])])


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Summarize saved adaptive benchmark runs")
    parser.add_argument("output_directory")
    parser.add_argument("run_directories", nargs="+")
    args = parser.parse_args()
    save_report(args.run_directories, args.output_directory)


if __name__ == "__main__":
    main()
