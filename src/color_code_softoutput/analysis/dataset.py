"""Column-projected Parquet access with centralized metric/failure semantics."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from ..simulation.storage import SHOT_SCHEMA, validate_shots

METRIC_FAILURES = {"selected_swim_distance":"ordinary_logical_error", "forced_gap":"comparative_logical_error"}
METRIC_FAILURES.update(ordinary_path_gap="ordinary_logical_error",
                       comparative_path_gap="comparative_logical_error",
                       ordinary_monotone_y_gap="ordinary_logical_error",
                       comparative_monotone_y_gap="comparative_logical_error")


class Phase2ADataset:
    """Open a run lazily and reject shards with incompatible schema or config.

    Args:
        run_directory: Directory containing metadata.json and shots/*.parquet.
    Raises:
        ValueError: Missing shards or mismatched Arrow schema/config metadata.
    """
    def __init__(self, run_directory: Path, *, shot_schema=SHOT_SCHEMA):
        self.run_directory = Path(run_directory)
        self.metadata = json.loads((self.run_directory / "metadata.json").read_text())
        self.shards = sorted((self.run_directory / "shots").glob("*.parquet"))
        if not self.shards:
            raise ValueError("No completed Parquet shards")
        for path in self.shards:
            schema = pq.read_schema(path)
            if not schema.equals(shot_schema, check_metadata=False):
                raise ValueError(f"Incompatible shot schema: {path}")
            if (schema.metadata or {}).get(b"config_hash", b"").decode() != self.metadata["config_hash"]:
                raise ValueError(f"Mismatched configuration hash: {path}")
        self._dataset = ds.dataset([str(p) for p in self.shards], format="parquet")

    def read(self, columns: list[str] | None = None, *, distance=None, physical_error_rate=None,
             rounds=None, noise_model_name=None) -> pd.DataFrame:
        """Read projected columns using exact stored grid values and Arrow filters.

        Args:
            columns: Needed fields only; None requests the full table.
            distance: Scalar or sequence of distances, or None for all.
            physical_error_rate: Scalar or sequence of stored probabilities.
            rounds, noise_model_name: Optional filters for schemas containing these dimensions.
        Returns:
            DataFrame containing the selected rows; source data are unchanged.
        """
        expression = None
        for name, value in (("distance", distance), ("physical_error_rate", physical_error_rate),
                            ("rounds", rounds), ("noise_model_name", noise_model_name)):
            if value is not None:
                values = [value] if np.isscalar(value) else list(value)
                term = ds.field(name).isin(values)
                expression = term if expression is None else expression & term
        return self._dataset.to_table(columns=columns, filter=expression).to_pandas()

    def available_values(self) -> dict[str, list]:
        """Return sorted distance and physical-probability values from the resolved grid."""
        config = self.metadata["resolved_config"]
        probabilities = ([config["physical_error_rate"]] if "physical_error_rate" in config else
                         config["near_threshold_ps"]+config["subthreshold_ps"])
        return {"distance":sorted(config["distances"]), "physical_error_rate":sorted(set(probabilities))}

    def metric_rows(self, metric: str, *, distance=None, physical_error_rate=None,
                    failure_column: str | None = None) -> pd.DataFrame:
        """Read one metric with its matching decoder label and stable shot identities.

        Args:
            metric: 'selected_swim_distance' or 'forced_gap'.
            distance: Optional distance selection.
            physical_error_rate: Optional probability selection.
            failure_column: Explicit nonstandard label override; None uses semantics.
        Returns:
            Projected rows sorted by stable config/batch/shot identity.
        Raises:
            ValueError: Unknown metric or failure column.
        """
        if metric not in METRIC_FAILURES:
            raise ValueError("Unknown confidence metric")
        failure = failure_column or METRIC_FAILURES[metric]
        if failure not in METRIC_FAILURES.values():
            raise ValueError("Unknown failure label")
        columns = ["config_id", "batch_id", "shot_index", "distance", "physical_error_rate", metric, failure]
        return self.read(columns, distance=distance, physical_error_rate=physical_error_rate).sort_values(
            ["config_id", "batch_id", "shot_index"])
