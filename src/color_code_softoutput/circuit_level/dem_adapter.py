"""Read the actual public color-code-stim decomposition; never rebuild Lee's DEM."""
import hashlib
import numpy as np
from scipy.sparse import csr_matrix
from color_code_stim.dem_utils.dem_manager import DemManager
from .graph import build_graph
from .model import DetectorMeta, RowRole, CircuitLevelGraph


def _binary(matrix):
    matrix = matrix.tocsr()
    matrix.data %= 2
    matrix.eliminate_zeros()
    return matrix


def adapt_stage2(manager: DemManager, color: str, *, closed_temporal_boundary: bool = True) -> CircuitLevelGraph:
    """Freeze H2, L2, weights and typed provenance from the unchanged hard path.

    Args:
        manager: Public ColorCode.dem_manager for ordinary triangular one-Z-
            observable memory; actual effective DEM/decomposition is consumed.
        color: 'r', 'g' or 'b'.
        closed_temporal_boundary: Must explicitly remain True; no open windows.
    Returns:
        Immutable labelled graph in hard H2 column order. Full source coordinate,
        time/color/Pauli metadata is retained also for virtual rows.
    Raises:
        ValueError: Matrix/source/metadata mismatch, invalid weights or unsupported
            mixed-source compression (not silently treated as a physical lift).
        NotImplementedError: Nontriangular, comparative, multi-observable or open input.
    Notes:
        Source IDs index error instructions in the manager's already X/Z-separated
        effective DEM, not individual physical circuit faults.
    """
    if not closed_temporal_boundary or manager.circuit_type != "tri" or manager.comparative_decoding:
        raise NotImplementedError("Only ordinary closed triangular memory is supported")
    if color not in "rgb" or len(color) != 1:
        raise ValueError("Color must be r, g or b")
    decomp = manager.dems_decomposed[color]
    H, p = decomp.Hs[1], np.asarray(decomp.probs[1])
    L = decomp.obs_matrix_stage2
    if manager.circuit.num_observables != 1 or L.shape != (1, H.shape[1]):
        raise NotImplementedError("Exactly one retained logical observable required")
    mapping = decomp.error_map_matrices[1].tocsr()
    if mapping.shape != (H.shape[1], manager.H.shape[1]) or np.any(np.diff(mapping.indptr) != 1):
        raise ValueError("Require one effective source per retained column")
    if len(set(map(int, mapping.indices))) != H.shape[1]:
        raise ValueError("Effective source map is not an injective column selection")
    expected_L = _binary((mapping.astype(np.uint8) @ manager.obs_matrix.T.astype(np.uint8)).T)
    if (expected_L != L).nnz:
        raise ValueError("Stage-2 labels differ from the hard outer observable map")
    # The existing symbolic path applies this parity formula even to a singleton;
    # retain its floating rounding instead of substituting the manager value.
    source_probabilities = manager.probs_xz[mapping.indices]
    if not np.array_equal(p, (1-(1-2*source_probabilities))/2):
        raise ValueError("Stage-2 probabilities are misaligned with effective sources")
    coords = manager.circuit.get_detector_coordinates()
    rows = []
    lam_r, lam_c = [], []
    for meta in decomp.stage2_rows:
        source_coords = tuple(tuple(coords[d]) for d in meta.source_detector_ids)
        if source_coords != meta.source_coordinates or any(len(x) < 5 for x in source_coords):
            raise ValueError("Detector coordinate provenance mismatch")
        role = RowRole(meta.role.value)
        if role == RowRole.VIRTUAL:
            actual_sources = tuple(map(int, decomp.Hs[0][:, meta.source_id].nonzero()[0]))
            if actual_sources != meta.source_detector_ids:
                raise ValueError("Virtual row differs from its actual H1 column")
        if role != RowRole.PADDING:
            for detector in meta.source_detector_ids:
                lam_r.append(detector)
                lam_c.append(meta.row_id)
        colors = tuple("rgb"[int(x[4])] for x in source_coords)
        paulis = tuple("XYZ"[int(x[3])] for x in source_coords)
        if role == RowRole.PHYSICAL and colors != (color,):
            raise ValueError("Physical row color mismatch")
        rows.append(DetectorMeta(meta.row_id, meta.source_id, role, meta.active,
                                meta.source_detector_ids, source_coords, colors, paulis,
                                tuple(x[2] for x in source_coords)))
    reconstruction = csr_matrix((np.ones(len(lam_r), dtype=np.uint8), (lam_r, lam_c)),
                                shape=(manager.H.shape[0], H.shape[0]))
    reconstructed = _binary(reconstruction @ H.astype(np.uint8))
    retained = _binary(manager.H.astype(np.uint8) @ mapping.T.astype(np.uint8))
    if (reconstructed != retained).nnz:
        raise ValueError("Manager detector map does not factor through actual H2")
    symbolic = decomp.dems_symbolic[1].error_map_matrix.tocsr()
    if np.any(np.diff(symbolic.indptr) != 1):
        raise ValueError("Unsupported symbolic source compression")
    unsorted = {int(source): i for i, source in enumerate(symbolic.indices)}
    model_hash = hashlib.sha256(str(manager.dem_xz).encode()).hexdigest()
    graph = build_graph(H, L.toarray().ravel(), np.log((1-p)/p), color=color, rows=rows,
                        probabilities=p, source_ids=tuple((int(x),) for x in mapping.indices),
                        unsorted_ids=tuple(unsorted[int(x)] for x in mapping.indices), model_id=model_hash)
    for edge, meta in zip(graph.mechanisms, decomp.stage2_edges, strict=True):
        if edge.column_id != meta.column_id or edge.endpoint_rows != meta.endpoint_rows or edge.source_dem_ids != meta.original_dem_ids:
            raise ValueError("Column metadata differs from actual H2/source mapping")
    return graph
