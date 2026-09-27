"""Saved-shot post-selection comparison; no decoding or new sampling.

Reduction is 1 - retained LER / each decoder's own unselected LER.
Competitiveness flags describe point estimates, not statistical equivalence.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

from .dataset import METRIC_FAILURES
from .path_gap import METRICS
from .postselection import postselection_curve
from .statistics import rounded_scores, wilson_interval


def compare_postselection(dataset, *, distance, physical_error_rate,
                          abort_rates=(0., .01, .025, .05, .1, .15, .2, .25, .3, .5),
                          competitive_margin=1.25, round_digits=None,
                          output_directory=None, metrics=METRICS, metric_display_name="Path-gap"):
    """Return/save long counts, side-by-side comparison and a Markdown report.

    Two policies are reported separately:
    * matched_abort: identical retained counts; boundary ties split by stable
      config/batch/shot ID, independent of labels;
    * whole_ties: most selective raw threshold not exceeding the abort budget.
      Actual abort fractions may differ: these are NOT matched-abort ratios.

    The configurable margin means residual LER <= margin * forced-gap LER.
    A point-estimate flag is not a noninferiority test. Zero reference failures
    give an undefined ratio, never a claim of equivalence. Wilson intervals are
    99% pointwise diagnostic intervals, not simultaneous or ratio intervals.
    """
    metrics = tuple(metrics)
    if (len(metrics) != 3 or len(set(metrics)) != 3 or metrics[-1] != "forced_gap"
            or any(m not in METRIC_FAILURES for m in metrics)
            or METRIC_FAILURES[metrics[0]] != "ordinary_logical_error"
            or METRIC_FAILURES[metrics[1]] != "comparative_logical_error"):
        raise ValueError("Expected ordinary/comparative metric pair followed by forced_gap")
    abort_rates = tuple(abort_rates)
    if not abort_rates or len(set(abort_rates)) != len(abort_rates) or any(
            not np.isfinite(a) or not 0 <= a < 1 for a in abort_rates):
        raise ValueError("Choose unique finite abort rates in [0,1)")
    if not np.isfinite(competitive_margin) or competitive_margin < 1:
        raise ValueError("Competitive margin must be finite and >= 1")
    ds = [distance] if np.isscalar(distance) else list(distance)
    ps = [physical_error_rate] if np.isscalar(physical_error_rate) else list(physical_error_rate)
    records = []
    identities = ["config_id", "batch_id", "shot_index"]
    for d in ds:
        for p in ps:
            reference_ids = None
            for metric in metrics:
                rows = dataset.metric_rows(metric, distance=d, physical_error_rate=p).sort_values(identities)
                if rows.empty or rows.duplicated(identities).any():
                    raise ValueError("Nonempty unique shot identities required")
                current_ids = rows[identities].reset_index(drop=True)
                if reference_ids is None:
                    reference_ids = current_ids
                elif not reference_ids.equals(current_ids):
                    raise ValueError("Metrics do not share identical physical shot IDs")
                scores = rounded_scores(rows[metric], round_digits)
                if not np.isfinite(scores).all():
                    raise ValueError("Finite scores required")
                failures = rows[METRIC_FAILURES[metric]].to_numpy(dtype=bool)
                n, base_errors = len(rows), int(failures.sum())
                baseline = base_errors/n
                order = np.argsort(-scores, kind="stable")
                cumulative = np.cumsum(failures[order])
                curve = postselection_curve(scores, failures)
                for abort in sorted(abort_rates):
                    # Integer abort budget; never discard more than requested.
                    kept = n-int(np.floor(abort*n + 1e-9))
                    eligible = curve[curve.retained_shots >= kept]
                    whole = eligible.iloc[-1]
                    for policy, count, errors, threshold in (
                        ("matched_abort", kept, int(cumulative[kept-1]), float(scores[order[kept-1]])),
                        ("whole_ties", int(whole.retained_shots), int(whole.retained_failures), float(whole.threshold)),
                    ):
                        rate = errors/count
                        low, high = wilson_interval(errors, count)
                        records.append(dict(distance=d, physical_error_rate=p, policy=policy,
                            target_abort_rate=abort, actual_abort_rate=1-count/n, metric=metric,
                            failure_column=METRIC_FAILURES[metric], shots=n,
                            baseline_failures=base_errors, baseline_ler=baseline,
                            retained_shots=count, retained_failures=errors, residual_ler=rate,
                            ler_low=float(low), ler_high=float(high), threshold=threshold,
                            boundary_tie_split=bool(count < np.count_nonzero(scores >= threshold)),
                            reduction_rate=1-rate/baseline if baseline else np.nan,
                            reduction_factor=baseline/rate if rate else np.nan))
    long = pd.DataFrame(records)
    keys = ["distance", "physical_error_rate", "policy", "target_abort_rate"]
    measures = ["actual_abort_rate", "baseline_ler", "retained_shots", "retained_failures",
                "residual_ler", "ler_low", "ler_high", "reduction_rate", "reduction_factor"]
    wide = long.pivot(index=keys, columns="metric", values=measures)
    wide.columns = [f"{metric}_{measure}" for measure, metric in wide.columns]
    wide = wide.reset_index()
    for metric in metrics[:2]:
        reference = wide.forced_gap_residual_ler
        ratio = wide[f"{metric}_residual_ler"].div(reference.where(reference > 0))
        wide[f"{metric}_ler_ratio_to_forced"] = ratio
        wide[f"{metric}_absolute_ler_excess"] = wide[f"{metric}_residual_ler"]-reference
        wide[f"{metric}_point_estimate_status"] = np.where(
            ratio.isna(), "undefined_zero_reference_failures",
            np.where(ratio <= competitive_margin, "within_margin_point_estimate", "above_margin_point_estimate"))
        wide[f"{metric}_low_count_warning"] = (
            (wide[f"{metric}_retained_failures"] < 20) | (wide.forced_gap_retained_failures < 20))
    directory = Path(output_directory or dataset.run_directory / "path_gap_comparison")
    directory.mkdir(parents=True, exist_ok=True)
    long.to_parquet(directory / "counts.parquet", index=False)
    wide.to_parquet(directory / "comparison.parquet", index=False)
    long.to_csv(directory / "counts.csv", index=False)
    wide.to_csv(directory / "comparison.csv", index=False)
    settings = dict(run_directory=str(dataset.run_directory.resolve()), distances=ds,
                    probabilities=ps, abort_rates=abort_rates, competitive_margin=competitive_margin,
                    round_digits=round_digits, confidence_level=.99, metrics=metrics, metric_display_name=metric_display_name,
                    reduction_definition="1 - residual_ler / decoder_baseline_ler",
                    policies=["matched_abort: stable shot-ID boundary tie break",
                              "whole_ties: largest attainable abort <= budget"],
                    inference="Descriptive point estimates; not an equivalence/noninferiority test")
    (directory / "settings.json").write_text(json.dumps(settings, indent=2)+"\n")
    report = _report(long, wide, settings)
    report_path = directory / "REPORT.md"
    report_path.write_text(report)
    return dict(counts=long, comparison=wide, report=report, report_path=report_path)


def _number(value, percent=False):
    if not np.isfinite(value):
        return "未定義"
    return f"{100*value:.2f}%" if percent else f"{value:.4g}"


def _report(counts, comparison, settings):
    metrics = settings["metrics"]
    ordinary, comparative, _ = metrics
    label = settings["metric_display_name"]
    lines = [f"# {label} post-selection 定量比較", "",
        f"Run: `{settings['run_directory']}`", "",
        "削減率 = 1 − 選別後LER / 各デコーダの選別前LER。削減倍率 = 選別前LER / 選別後LER。",
        "残存LER比 = path-gap LER / forced-gap LER（小さいほど良い、1で同じ）。",
        f"参考判定の許容倍率は {settings['competitive_margin']:g}。これはユーザー指定可能な記述的基準で、統計的な同等性の証明ではありません。", "",
        "ordinary path-gap 対 forced gap は異なる hard decoder のパイプライン比較。comparative path-gap 対 forced gap は同じ hard decoder のスコア比較。",
        "各手法の残存失敗数・99% Wilson区間は counts.csv に保存。20未満の残存失敗数には低カウント警告を付ける（20は検定基準ではない）。",
        "両方ゼロ失敗でも同等とは判定しない。forced gapがゼロ失敗なら比は未定義。ゼロ失敗時の削減率100%も観測値のみで、真のLERがゼロという意味ではない。", "",
        "## 同一 abort rate（境界同点のみ shot ID で分割）", "",
        "| d | p | abort | ordinary 残存失敗 | forced 残存失敗 | ordinary 削減率 | forced 削減率 | ordinary/forced LER | comparative/forced LER | 低カウント |",
        "|---|---|---|---|---|---|---|---|---|---|"]
    matched = comparison[comparison.policy == "matched_abort"]
    for row in matched.itertuples():
        lines.append(f"| {row.distance} | {row.physical_error_rate:g} | {_number(getattr(row, ordinary + '_actual_abort_rate'), True)} | {int(getattr(row, ordinary + '_retained_failures'))} | {int(row.forced_gap_retained_failures)} | {_number(getattr(row, ordinary + '_reduction_rate'), True)} | {_number(row.forced_gap_reduction_rate, True)} | {_number(getattr(row, ordinary + '_ler_ratio_to_forced'))} | {_number(getattr(row, comparative + '_ler_ratio_to_forced'))} | {'あり' if getattr(row, ordinary + '_low_count_warning') or getattr(row, comparative + '_low_count_warning') else 'なし'} |")
    lines += ["", "## 記述的な判定（abort > 0 の設定点）", ""]
    positive = matched[matched.target_abort_rate > 0]
    for metric in metrics[:2]:
        statuses = positive[f"{metric}_point_estimate_status"].value_counts().to_dict()
        lines.append(f"- {metric}: {statuses}")
    lines += ["", "### 距離ごとの読み取り", ""]
    for (d, p), group in positive.groupby(["distance", "physical_error_rate"]):
        parts = []
        for row in group.itertuples():
            if row.target_abort_rate in (.05, .1, .2):
                parts.append(f"abort {_number(getattr(row, ordinary + '_actual_abort_rate'), True)}: ordinary/forced={_number(getattr(row, ordinary + '_ler_ratio_to_forced'))}（残存失敗 {int(getattr(row, ordinary + '_retained_failures'))}/{int(row.forced_gap_retained_failures)}）")
        if parts:
            lines.append(f"- d={d}, p={p:g}: " + "; ".join(parts))
    defined = positive[f"{ordinary}_ler_ratio_to_forced"].dropna()
    if len(defined) and (defined > settings['competitive_margin']).any():
        lines += ["", "ordinary path-gap は全設定でforced gap並みとはいえない。許容倍率を超える点があり、距離・棄却率によって相対性能が変わる。一部の点で比が1以下でも、全体としての優越性は意味しない。"]
    else:
        lines += ["", "定義可能な点推定を個別に確認すること。許容範囲内の点推定だけでは統計的同等性を証明できない。"]
    lines += ["", "設定点は互いに独立ではなく、この件数は統計検定ではない。距離・abort rateごとに評価し、低カウント領域の順位は確定しない。", "",
        "## 元の図との対応", "",
        "元の図は同点を全保持する threshold 曲線。matched_abort 表は境界同点を分けるので、その点が図上の閾値として存在するとは限らない。",
        "whole_ties 表は指定abort予算以下で最大の閾値を選択。actual_abort_rate を確認すること：手法間で同じ棄却率とは限らない。補間で存在しない閾値を作ってはいない。",
        "生スコアはデフォルトで丸めない。浮動小数点の微差も順位に残る。round_digits を変える場合は別出力先を指定し、感度を確認する。", "",
        "99%区間は点ごとのLER診断であり、比・削減率・手法間差や曲線全体の信頼区間ではない。性能比較は保存ショットの事後的な記述で、較正・普遍的な優越性・統計的同等性を主張しない。"]
    return "\n".join(lines).replace("path-gap", label).replace("path gap", label)+"\n"
