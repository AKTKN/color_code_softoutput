# Phase 2 implementation package

This directory contains the implementation plan for integrating a color-code stage-2 swim-distance calculation into the concatenated-MWPM workflow.

We first do integration of calculating swim-distance for color code in PyMatching so that color0code-stim can use it.
After that, we will full simulation programs in `src`, using external_libs.  

The plan is based on the Phase-1 theory developed in `note.tex` and on a live code inspection of:

- `seokhyung-lee/color-code-stim` — inspected `main` at `0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`.
- `Zihan-Chen-PhMA/PyMatching` — inspected `master` at `2abf455ef58ee67c4232e7896e1468e7c983f372`; soft-output feature commit `4497499196a30b4fb5e872b9f169866f19bc145e`.
- `AKTKN/concatenated-decoder` — inspected `main` at `8f817004a5a28a219767f71d048235bd48a5ad9b`.

## Files

- `IMPLEMENTATION_REPORT.md`: current architecture and relevant implementation details of the three repositories, plus identified implementation risks.
- `INTEGRATION_PLAN.md`: proposed architecture, interfaces, implementation milestones, and initial numerical experiment.
- `TEST_PLAN.md`: correctness gates and tests required at each milestone.
- `AGENTS.md`: source-level instructions for Codex during Phase 2A.
- `CODEX_PHASE2_IMPLEMENTATION_PROMPT.md`: prompt for the first Codex implementation campaign.

## Primary Phase-2A objective

Implement the MWPM fixed-color stage-2 swim distance for triangular color-code memory experiments without changing the existing concatenated decoder's hard decision or ordinary solution weights.

The initial numerical study should measure the per-color swim-distance distribution, conditional logical error rate, post-selection performance, comparison with the existing comparative-decoding logical gap, and runtime overhead.

## Scope warning

The Phase-1 theorem is a fixed-color, fixed-stage-1-fiber result. A per-color swim distance must not be silently reinterpreted as a full-decoder logical gap or a logical-class posterior LLR.

The software should preserve detector/time/error-mechanism metadata for a later circuit-level extension, but circuit-level boundary grouping must remain unimplemented or explicitly `UNCLASSIFIED` until the corresponding topology is verified.
