"""Global DEM adapters for the optional Tesseract decoder."""

import numpy as np


OPTIONS = frozenset({
    "det_beam", "beam_climbing", "no_revisit_dets", "verbose", "merge_errors",
    "pqlimit", "det_orders", "det_penalty", "create_visualization",
    "sparsify_errors", "sparsify_base_degree", "sparsify_max_degree",
    "sparsify_reactivate_limit", "num_det_orders", "det_order_method", "seed",
    "xyz_decoding",
})


def detector_error_model(code, options):
    """Select the requested global DEM without triggering unrelated decoders.

    ``xyz_decoding`` is local workflow control, not a ``TesseractConfig``
    argument.  Its true path deliberately reads the physical circuit directly,
    so ``ColorCode.dem_xz`` and its depolarizing-error separation remain lazy.
    """
    if dict(options).get("xyz_decoding", False):
        return code.circuit.detector_error_model(flatten_loops=True)
    return code.dem_xz


def compile_tesseract(dem, options):
    """Compile once per cached circuit; preserve the supplied DEM as-is."""
    from tesseract_decoder import tesseract, utils

    options = dict(options)
    options.pop("xyz_decoding", None)
    if "det_order_method" in options and isinstance(options["det_order_method"], str):
        name = options["det_order_method"]
        try:
            options["det_order_method"] = getattr(utils.DetectorOrderMethod, name)
        except AttributeError as exc:
            raise ValueError(f"unknown Tesseract detector order method: {name}") from exc
    if "det_orders" in options and options["det_orders"] is not None:
        options["det_orders"] = [list(order) for order in options["det_orders"]]
    return tesseract.TesseractConfig(dem=dem, **options).compile_decoder()


def decode_tesseract(decoder, detectors, num_observables):
    """Call the single-shot API and check observable order and shape."""
    predictions = []
    for syndrome in detectors:
        prediction = np.asarray(decoder.decode(np.asarray(syndrome, dtype=bool)), dtype=bool)
        if prediction.shape != (num_observables,):
            raise ValueError("Tesseract prediction does not match selected DEM observables")
        predictions.append(prediction)
    return np.asarray(predictions, dtype=bool)
