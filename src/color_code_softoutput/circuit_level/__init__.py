"""Closed-memory fixed-fiber swim; selected-color confidence remains uncertified."""
from .model import CircuitLevelGraph, CircuitLevelTopology, CircuitLevelSwimResult, Witness
from .dem_adapter import adapt_stage2
from .logical_topology import preprocess_topology
from .coverage import residual_weights
from .swim import compute_circuit_level_swim
from .decoder import CircuitLevelDecoder
from .experiment import CircuitLevelMemoryConfig

__all__ = ["CircuitLevelGraph", "CircuitLevelTopology", "CircuitLevelSwimResult", "Witness",
           "adapt_stage2", "preprocess_topology", "residual_weights", "compute_circuit_level_swim",
           "CircuitLevelDecoder", "CircuitLevelMemoryConfig"]
