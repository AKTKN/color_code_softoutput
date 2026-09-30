# Tesseract XYZ global-DEM decoding report

Date: 2026-09-30

## Result

The canonical YAML simulation accepts the following Tesseract-local option:

```yaml
color_code_options:
  temp_bdry_type: Y

decoders:
  - type: tesseract
    options:
      xyz_decoding: true
      det_beam: 5
```

`xyz_decoding` defaults to `false`. The two DEM routes are:

| option | DEM supplied to Tesseract |
| --- | --- |
| omitted or `false` | Existing `ColorCode.dem_xz` |
| `true` | `ColorCode.circuit.detector_error_model(flatten_loops=True)` |

The true route is the unseparated global circuit DEM. It does not call the
project-specific `separate_depolarizing_errors` conversion. It therefore keeps
the X/Z-correlated error mechanisms produced by Stim from the original circuit
noise instead of first replacing depolarizing instructions by separate X- and
Z-type circuit instructions.

## Implementation

### Configuration

- Added `xyz_decoding` to the allowed Tesseract YAML options.
- Required its value to be a YAML boolean.
- Retained rejection of `decode_options`, including BP predecoding.
- Retained rejection of color-correlated, relifting, perturbation and
  comparative ColorCode decoder modes.
- A Y temporal boundary is accepted only with `xyz_decoding: true`; the old
  X/Z-only rule remains for the default route.

### DEM selection and compilation

`simulation.tesseract.detector_error_model` owns the DEM selection. In XYZ
mode it reads the physical `ColorCode.circuit` directly. Because `ColorCode`
creates its `DemManager` lazily, this avoids accessing `ColorCode.dem_xz` and
therefore avoids all of the following:

- `separate_depolarizing_errors`;
- X/Z DEM construction;
- color and stage-1/stage-2 decomposition;
- BP decoding and BP posterior priors;
- perturbation or candidate reweighting.

`xyz_decoding` is removed before constructing `TesseractConfig`, because it is
workflow control rather than a native Tesseract argument. The selected
`stim.DetectorErrorModel` is otherwise passed unchanged to
`TesseractConfig(dem=...).compile_decoder()`.

The worker validates both `num_detectors` and `num_observables` against the
sampled Stim circuit. It stores the selected DEM's observable count with the
compiled decoder, so XYZ shot decoding never causes a later accidental access
to `ColorCode.dem_xz`. Tesseract continues to decode one boolean syndrome row
at a time and the workflow continues to save only `logical_error.parquet`.

### Compatibility

The missing/false setting preserves the previous X/Z-separated DEM route and
its configuration semantics. The decoder cache key already contains all
Tesseract options, so XYZ and X/Z points cannot share a compiled decoder.

Documentation and the commented YAML example were updated.

## Validation

Environment:

- Python environment: `color_code_so`
- Stim: 1.16.0
- Tesseract decoder: 0.1.1.dev20260910235247

Focused Tesseract tests:

```text
pytest -q tests/test_simulation_tesseract.py
6 passed in 14.55s
```

These tests cover boolean validation, default-route DEM identity, rejection of
Y without XYZ mode, acceptance of Y with XYZ mode, raw-circuit DEM selection,
absence of `dem_xz` access, prediction association and real native-extension
end-to-end runs for both the old X/Z route and the new Y/depolarizing XYZ
route.

After rebuilding the existing local PyMatching extension to match its checked-
out Python source, the combined Tesseract and native-workflow focus passed:

```text
13 passed in 33.56s
```

The rebuild was required because the pre-existing binary exposed the older
five-argument perturbation binding while the checked-out Python source called
the current six-argument binding. No PyMatching source was changed.

Complete root regression:

```text
402 passed in 226.60s
```

An independent d=3, one-round, Y-boundary, `NoiseModel(depol=0.01)` check gave:

```text
after raw global DEM selection: DemManager = None
raw DEM: 6 detectors, 1 observable, 7 error instructions
after X/Z DEM selection: DemManager = DemManager
raw DEM == X/Z DEM: False
raw SHA-256: cfd8c15b24eefdeb4d809cbd1da0eb2a47f537c0321de0955123a83b99071d64
X/Z SHA-256: 1ac76099101056b00d90d4bf0e6bceed6b181f9813cd4a83ff811a70c9f10309
```

This confirms that XYZ mode selects a different, unseparated model and does
not merely rename the existing `dem_xz` object.

## Scope

This change provides a joint global-DEM input to Tesseract. It does not use BP,
does not alter the physical sampling circuit, and does not change the
concatenated-matching decoder. No logical-error-rate improvement, calibration,
or runtime advantage is inferred from the smoke tests.
