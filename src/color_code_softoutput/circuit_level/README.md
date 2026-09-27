# Closed-memory circuit-level swim

Use the `color_code_so` environment with the existing Phase-2A editable external
packages. Neither external repository needs a change.

```python
from color_code_stim import ColorCode, NoiseModel
from color_code_softoutput.circuit_level import CircuitLevelDecoder

code = ColorCode(d=5, rounds=5, circuit_type="tri", cnot_schedule="tri_optimal",
                 noise_model=NoiseModel.uniform_circuit_noise(0.003))
decoder = CircuitLevelDecoder(code)
detectors, actual = code.sample(32, seed=20260916)
prediction, extra = decoder.decode(detectors, return_witness=True)
print(extra["selected_swim_distance"])
print(decoder.diagnostics())
```

The public ordinary hard result is returned unchanged. A cached replay of the
actual public H1/H2 matrices reads growth through the existing PyMatching API;
every selected hard prediction, ordinary weight, color and correction must
match. This extra decoding work is intentional and included in runtime.
The old external `ColorCode.decode(compute_swim_distance=True)` remains the
code-capacity API; circuit callers use `CircuitLevelDecoder`.

`dem_adapter.py` validates the actual retained effective matrices, observable
projection, source selection, probability sorting and detector metadata.
`graph.py` freezes every column, including parallel mechanisms and loops.
`logical_topology.py` caches class existence and balance; balanced graphs use
the cut, others the logical cover. `coverage.py` propagates original-graph
balls before transport. `swim.py` computes the exact residual objective and
`validation.py` checks witnesses against original binary incidence/labels.
`decoder.py` provides the read-only hard/growth integration.

For supplied synthetic/retained graph models, `build_graph`,
`preprocess_topology`, `residual_weights` and `compute_circuit_level_swim`
are separate pure operations. Missing growth is an error. A missing opposite
class returns `no_opposite_class`, infinity and no witness. Returned witnesses
are original-column mod-two supports, also at zero residual cost. Coordinate
metadata never determines the logical label.

Small reproducible validation:

```bash
conda run -n color_code_so python -m pytest tests/circuit_level -q
conda run -n color_code_so python -m color_code_softoutput.experiments.circuit_level_memory_test --smoke
conda run -n color_code_so python -m color_code_softoutput.experiments.circuit_level_memory_test --shots 2000 --workers 3 --batch-size 250 --analyze
```

The default grid is d=3,5,7, rounds=d, p=.003, 2000 shots per point. This is an
implementation-validation point, not paper reproduction. The runner reuses
the shared bounded worker pool, deterministic seed recipe, atomic Parquet
writer, source archives and existing distribution/conditional-LER/postselection
plotters. Open saved runs with `analysis.circuit_level.CircuitLevelDataset`.
The thin notebook is `notebooks/circuit_level_getting_started.ipynb`.

The notebook's final cell audits which color supplies the two minima used by
comparative decoding.  Because legacy shot shards contain only the final gap,
`python -m color_code_softoutput.experiments.comparative_color_origin RUN_DIR`
can deterministically replay their saved seeds and write all six class/color
weights to `RUN_DIR/comparative_candidates/*.parquet`.  The analysis verifies
the reconstructed prediction and gap before reporting same/different-color
counts.  Original shot shards are not rewritten.

The source model is color-code-stim's actual X/Z-separated, graphlike-filtered
effective DEM, which differs from both the correlated physical noise law and
the paper's literal filtering order. Physical samples still come from the
original uniform-noise circuit. All per-color values remain in storage;
selected swim is never replaced by min over colors. The paired `forced_gap`
is the existing comparative logical gap, with its own failure labels.

Weights and radii are in natural-log odds. Witness comparison uses absolute
1e-9 and relative 1e-10 tolerances; hard values are compared exactly. Backend
weight quantization is distinct from labelled-column cost. Growth is the
existing final-defect metric-ball convention, not a certified optimal odd-cut
dual: `swim_bound_certified=False`. No posterior calibration, threshold result,
family-wide balance theorem, open temporal boundary or sliding window is claimed.
