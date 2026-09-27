# Adaptive near-optimal decoder: 実行順序

この README は `prompts/00_README.md` の新しい 6 段階に対応する。以前の
`prompts/color_correlated/00–06` ワークフローは別の完了済みパイプラインであり、
このランナーでは実行しない。

実行前に `prompts/near_optimal_color_code_theory.tex` を読む。各段階の
Codex にもこのファイルの絶対パスを渡す。ローカルの未コミット変更を先に確認し、
特に color-correlated decoder と `color_correlated_run.parquet` の作業を保持する。

| 段階 | prompt | 主な作業先 | 完了条件 |
| --- | --- | --- | --- |
| 01 | `01_shared_candidate_scoring.md` | `external_libs/color-code-stim` | 共通の候補採点、既存動作の回帰テスト |
| 02 | `02_cross_color_relifting.md` | `external_libs/color-code-stim` | 適応的 relifting、Stage-2 syndrome 再利用、テスト |
| 03 | `03_xz_dem_perturbation_ensemble.md` | `external_libs/color-code-stim` | 共通 X/Z DEM 摂動、全色再分解、テスト |
| 04 | `04_integration_regression.md` | decoder とルート | 排他設定、既存 color-correlated 動作の保持、統合テスト |
| 05 | `05_softoutput_experiment_integration(1).md` | ルートと decoder | 対応する `relift_run.parquet`、paired smoke、診断分析 |
| 06 | `06_ablation_benchmark.md` | ルートと decoder | アブレーション集計と図、bounded smoke のみ |

Prompt 5 の実ファイル名には `(1)` が含まれる。ランナーはこの名前をそのまま参照する。

## tmux で連続実行

```bash
prompts/scripts/run_codex_pipeline.sh --list
prompts/scripts/start_codex_pipeline_tmux.sh
prompts/scripts/codex_pipeline_status.sh
tmux attach -t codex-near-optimal
```

`start_codex_pipeline_tmux.sh` は引数をランナーへ渡す。例えば、段階 03 から
再実行する場合は次の通り。

```bash
prompts/scripts/start_codex_pipeline_tmux.sh --from 03
```

各段階は構造化 JSON の `status=success` かつ `next_stage_safe=true` でのみ
次へ進む。エラー時はその段階で停止し、変更とログを保持する。結果は
`.codex-pipeline/near-optimal/results/`、標準出力とエラーは同階層の
`stdout/` と `stderr/`、tmux 全体のログは `pipeline.log` に保存する。
`exit-code` にはランナーの終了コードが記録される。

通常実行は既存の未コミット変更を許容し、Git の commit/push は行わない。
チェックポイントを自動作成する場合だけ `--checkpoint` を渡す。この場合は
開始時にルートと decoder の両リポジトリがクリーンであることが必要で、
成功段階ごとに変更があったリポジトリへ個別のローカル commit を作る。
現在のルートには進行中の変更があるため、そのまま実行する場合は通常モードを使う。

`--from` は段階の前提条件を自動検証しない。指定した前段階の成果を確認してから
使う。大規模サンプリング、push、merge はこのパイプラインに含まれない。
