# Saved global-BP run analysis compatibility (2026-09-29)

The original workspace on `codex/native-stage1-perturbation-20260929`
now reads saved global-BP runs without switching decoder sources. The BP
decoding implementation remains in `color_code_softoutput_bp_global`.

## Changes

- `simulation/config.py` accepts saved `bp_predecoding` and `bp_prms`,
  validates flags/parameter names and preserves the parameter mapping when
  serializing configuration metadata.
- `analysis/color_correlated.py` validates the BP sidecar and requires
  concatenated-metric null masks to equal convergence flags. At the user's
  correction, `shots` always counts all physical shots. LER is the saved
  True count divided by this total; nulls are excluded from the numerator
  and retained in the denominator. `statistics_scope` is `all shots`.
  All-converged files with all-null labels have a zero saved True count
  and retain the total shot count/Wilson denominator.
- Baseline overlays and improvement ratios retain the original selection
  by physical configuration, without BP-specific restrictions or aliases.
  Paired methods keep their own baseline. The earlier conditional-LER and
  separate-baseline changes were unauthorized and have been reversed.
- `analysis/workflow_soft_output.py` validates score/failure/convergence
  masks, excludes skipped shots, labels conditional statistics and rejects
  pooling different BP sampling scopes in a group. All-converged score
  groups report that no scored shots are available.

Null logical-error outcomes cannot be reconstructed from the convergence
flag. The requested saved True count / total-shot aggregation does not
recover those outcomes or rewrite nulls as successful labels. Existing
non-BP saved schemas and statistics are preserved.

## Verification

Environment: `/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python`,
with `PYTHONPATH=src` in the original workspace.

```sh
PYTHONPATH=src /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest -q tests/test_bp_saved_run_analysis.py tests/test_color_correlated_analysis.py tests/test_color_correlated_comparison.py tests/test_workflow_soft_output.py tests/test_workflow_soft_output_plots.py
# 49 passed in 28.29s after the user's correction
```

The 13 independently constructed saved-Parquet cases cover config metadata,
total-shot denominators/original baseline selection, different BP settings,
all-converged data, corrupted sidecars/indices/masks, additional sources,
soft-output plots and rejection of null non-BP metrics. Existing analysis
tests also pass. The preceding conditional-LER version passed 374 root tests;
the correction was verified with the 49 affected analysis tests above.

Read-only validation used the actual saved run
`results/bpmatching/26_09_29_20_26_20_449d8157`: all 36 point counts and BP
null masks agree with direct Parquet reads. Each point has 10,000 physical
shots and uses 10,000 as the LER denominator. Direct Parquet True counts
agree at all 36 points. The baseline overlay has 45 rows and only the
original `baseline` alias; LER and improvement plots at p=.03/.04/.05 pass.
For d5/p=.03, BP_MWPM has 54 saved True values, yielding 54/10000=.0054.
The unmodified notebook's first cell and summary also passed the preceding
compatibility verification.

Hashes before/after verification confirm the saved Parquet/log files and
the user-edited notebook were unchanged. Notebook SHA256:
`1cab6c5650750e68a6857672e4b85640a9637f8043f5921a5da080dac6f37bd1`.
The external decoder/PyMatching checkouts were not changed. No new benchmark
was launched.

Rerun the notebook's first cell, or restart the kernel and rerun analysis.
The current improvement cell selects p=.002, absent from this run; select
p=.03, .04 or .05. Its other settings and user edits were preserved.
