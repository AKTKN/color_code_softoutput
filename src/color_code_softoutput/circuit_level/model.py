"""Immutable records for one-observable retained closed-memory DEM graphs.

Vertex/edge indices are dimensionless; all weights/radii use natural-log odds.
Tuples own their data, so preprocessing cannot silently track mutated matrices.
"""
from dataclasses import dataclass
from enum import Enum


class RowRole(str, Enum):
    """Constrained physical/virtual rows and explicitly inactive storage padding."""
    PHYSICAL = "PHYSICAL_C_DETECTOR"
    VIRTUAL = "STAGE1_VIRTUAL"
    PADDING = "INACTIVE_PADDING"


class BoundaryRole(str, Enum):
    """Algebraic endpoint roles; no spatial/temporal logical inference is made."""
    INTERNAL = "internal"
    MATCHING = "artificial_matching_boundary"
    LOOP = "zero_detector_loop"


class TopologyMethod(str, Enum):
    """Exact algorithms for the one-bit fixed-fiber objective."""
    TWO_BOUNDARY = "two_boundary"
    LOGICAL_COVER = "logical_cover"


class SwimStatus(str, Enum):
    """A missing opposite class is distinct from a zero-cost logical witness."""
    OK = "ok"
    NO_OPPOSITE_CLASS = "no_opposite_class"


@dataclass(frozen=True)
class DetectorMeta:
    """One H2 row and all its physical detector sources.

    Args:
        row_id, source_id: Original H2 row and physical/restricted-column ID.
        role, active: Constraint type and nonzero-incidence flag.
        detector_ids, coordinates: Aligned tuples of source detector IDs and
            complete package coordinates (x,y,time,Pauli,color,...).
        colors, paulis, times: Aligned typed source attributes, not logical labels.
    """
    row_id: int
    source_id: int
    role: RowRole
    active: bool
    detector_ids: tuple[int, ...] = ()
    coordinates: tuple[tuple[float, ...], ...] = ()
    colors: tuple[str, ...] = ()
    paulis: tuple[str, ...] = ()
    times: tuple[float, ...] = ()


@dataclass(frozen=True)
class Stage2Mechanism:
    """One retained column, including parallel edges and zero-detector loops.

    Args:
        column_id: Position in the actual sorted H2, unique within a graph.
        stable_id: Model-hash/color/source identity, stable across reconstruction.
        endpoints: Two completed base vertex indices (a loop repeats b_star).
        endpoint_rows: Original nonzero H2 row IDs, length zero, one or two.
        logical_label: L2 column bit, independent of coordinates.
        probability, weight: Effective mechanism probability and natural-log odds.
        source_dem_ids: Manager effective DEM error-instruction ordinals.
        unsorted_column_id: Column position before the hard probability sort.
        boundary_role: Algebraic incidence role only.
    """
    column_id: int
    stable_id: str
    endpoints: tuple[int, int]
    endpoint_rows: tuple[int, ...]
    logical_label: int
    probability: float
    weight: float
    source_dem_ids: tuple[int, ...]
    unsorted_column_id: int
    boundary_role: BoundaryRole


@dataclass(frozen=True)
class CircuitLevelGraph:
    """Frozen labelled graph; b_star is len(active_rows), never a measured row.

    Args:
        color, model_id: Branch label and effective-model SHA256.
        rows: Metadata for every original H2 row, including padding.
        active_rows: Original row IDs in analysis vertex order.
        mechanisms: Every H2 column in original column order.
        original_shape: H2 shape before omitting zero rows.
        closed_temporal_boundary: Must be True for this implementation.
    """
    color: str
    model_id: str
    rows: tuple[DetectorMeta, ...]
    active_rows: tuple[int, ...]
    mechanisms: tuple[Stage2Mechanism, ...]
    original_shape: tuple[int, int]
    closed_temporal_boundary: bool = True

    @property
    def b_star(self) -> int:
        """Return the sole artificial matching endpoint index (dimensionless)."""
        return len(self.active_rows)

    @property
    def num_vertices(self) -> int:
        """Return completed vertex count, including b_star."""
        return self.b_star + 1

    @property
    def weights(self) -> tuple[float, ...]:
        """Return weights in H2 column order, in natural-log odds."""
        return tuple(e.weight for e in self.mechanisms)


@dataclass(frozen=True)
class AnalysisGraph:
    """Cached adjacency, each arc (neighbor, source_column_id); weights arrive per shot."""
    adjacency: tuple[tuple[tuple[int, int], ...], ...]
    pairs: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class CircuitLevelTopology:
    """Shot-independent class/balance results and prebuilt selected analysis graph.

    Potential is indexed by real vertices; obstruction IDs are inconsistent
    non-tree edges, not the total number of odd cycles in the graph.
    """
    graph: CircuitLevelGraph
    class_exists: bool
    balance_passed: bool
    potential: tuple[int, ...]
    odd_cycle_obstructions: tuple[int, ...]
    method: TopologyMethod | None
    analysis: AnalysisGraph | None


@dataclass(frozen=True)
class Witness:
    """Mod-two original-column support and stable IDs; cost is in residual weight units."""
    column_ids: tuple[int, ...]
    stable_ids: tuple[str, ...]
    cost: float


@dataclass(frozen=True)
class CircuitLevelSwimResult:
    """Fixed-fiber geometric result, never an exact posterior or certified gap.

    phi is +inf and witness None for no_opposite_class. A finite zero may have
    a nonempty witness. certification_flag is always False in this implementation.
    """
    phi: float
    witness: Witness | None
    method: TopologyMethod | None
    class_exists: bool
    balance_passed: bool
    status: SwimStatus
    certification_flag: bool = False
