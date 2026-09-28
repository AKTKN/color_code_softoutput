# Saved-run decoder identity audit — 2026-09-28

Run: `cluster_results/26_09_28_14_38_26_779e2a31`.

The plotted alias `concat_mwpm` is configured as `type: color_correlated`,
`enable_colorcorrelated_decoding: true`, `color_correlated_b: 2.0` and
`remove_non_edge_like_errors: true`. There is no ordinary `type: concat_mwpm`
entry in this saved run. An alias is a label; it does not change the decoder
implementation selected by type/options. The apparent ordinary-vs-ordinary
LER discrepancy is therefore a comparison of two different methods.

## Code trace

- Saved configuration: `run_log.json`, decoder entry at lines 47–58.
- `simulation/worker.py::_construct` constructs the configured decoder from
  its options and separately constructs the baseline with
  `enable_colorcorrelated_decoding=False`. Here, the unspecified final
  selection basis resolves to `original_dem` for color-correlated decoding
  and `stage2` for the ordinary baseline. Both circuits are checked equal.
- `simulation/worker.py::run_chunk` samples once and feeds the same detector
  array to configured and baseline decoding. Both failures are computed
  against the same sampled actual observable. They are stored in
  `logical_error.parquet` and `default_logical_error.parquet` respectively.
- `ConcatMatchingDecoder` runs three ordinary candidates, then the scheduled
  extra guided candidates. With b=2, guide-selected original DEM source
  probabilities are raised to `sqrt(q)` for stage 1. Stage 2 retains base
  priors; final selection uses original DEM log odds. This is additional
  decoding, not merely another name for ordinary concatenated matching.
- `analysis/color_correlated.py::_ler_table` gives color-correlated baseline
  sources priority over perturbation sources. In this run, all 15 displayed
  baseline points come from alias `concat_mwpm`, type `color_correlated`.
  Thus the plotted baseline and `concat_mwpm` curves use the same shots.

## Saved-array verification

Each row has 1,000,000 shots. Rescued = baseline fails and final succeeds;
worsened = baseline succeeds and final fails. Read both saved failure arrays
for all 15 points and checked the rescue array element by element. Every
saved effect count agrees; baseline failures minus final failures equals
rescued minus worsened at every point.

| d | p | Baseline failures | Alias concat_mwpm failures | Rescued | Worsened | Net rescued |
|---|---|---|---|---|---|---|
| 7 | 0.020 | 585 | 540 | 52 | 7 | 45 |
| 7 | 0.025 | 1364 | 1274 | 106 | 16 | 90 |
| 7 | 0.030 | 2672 | 2511 | 186 | 25 | 161 |
| 7 | 0.035 | 4690 | 4456 | 283 | 49 | 234 |
| 7 | 0.040 | 7730 | 7382 | 450 | 102 | 348 |
| 9 | 0.020 | 160 | 131 | 29 | 0 | 29 |
| 9 | 0.025 | 483 | 400 | 89 | 6 | 83 |
| 9 | 0.030 | 1196 | 1003 | 220 | 27 | 193 |
| 9 | 0.035 | 2409 | 2023 | 443 | 57 | 386 |
| 9 | 0.040 | 4351 | 3806 | 666 | 121 | 545 |
| 11 | 0.020 | 60 | 45 | 19 | 4 | 15 |
| 11 | 0.025 | 162 | 110 | 58 | 6 | 52 |
| 11 | 0.030 | 561 | 412 | 170 | 21 | 149 |
| 11 | 0.035 | 1233 | 930 | 351 | 48 | 303 |
| 11 | 0.040 | 2483 | 1961 | 634 | 112 | 522 |

For d=9, p=.04, the two rates are .004351 and .003806. Their count difference
545 is exactly 666 rescued minus 121 worsened shots. It is not a discrepancy
between independent samples of the same decoder.

## Bounded current-code check

Using decoder main `072a87d294ed2e9388d1843a1065b41aff043ba4`, reconstructed
all 15 physical conditions from the saved configuration and checked 128
common shots per condition (1,920 transient correctness shots total; seed
20260928). The configured/ordinary circuits and original X/Z DEMs agree.
Ordinary decoding agrees shot by shot with selecting the color-correlated
branch's first three unmodified candidates by their native stage-2 weights.
For this one-round uniform bit-flip setting, native/base-original selection
weights for those three candidates differ only at floating-point precision
(maximum observed absolute difference 1.066e-14). Guided candidates were
scheduled in every condition. No baseline-vs-final prediction differences
occurred in this small local sample; it is a code-path check, not a new LER
estimate or a replay of the cluster shots.

Executed with:

```bash
PYTHONPATH="$PWD/external_libs/color-code-stim/src:$PWD/src" /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python /tmp/audit_decoder_baseline_779e2a31.py
```

Detailed transient audit results: `/tmp/decoder-baseline-audit-779e2a31.json`.
The saved run log records no decoder-source Git SHA, and the raw detector
shots/chunk schedule are not saved in the canonical metric files. Exact
historical-source replay cannot be established from that log alone; the
configuration identity and saved failure-array checks do not require replay.

## Configuration for a future ordinary-decoder comparison

```yaml
decoders:
  - decoder_alias: concat_mwpm
    type: concat_mwpm
    options:
      enable_colorcorrelated_decoding: false
      color_correlated_weight_basis: stage2
      remove_non_edge_like_errors: true
```

Retain the extra color-correlated entry under an informative alias such as
`color_correlated_b2` if that method should also be compared. The historical
run log and metric paths were left unchanged: aliases participate in saved
paths and point identities, so changing the log's alias alone would break
catalog/path consistency. No production decoder change is indicated by this
audit; it identifies a mismatch between the label and configured method.
