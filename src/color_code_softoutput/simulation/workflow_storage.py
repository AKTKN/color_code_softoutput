"""Bounded, main-process Parquet storage for one planned YAML workflow point."""

from bisect import bisect_left
from dataclasses import dataclass
from pathlib import Path
import os

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from .planner import point_directory_name
from .task import ResolvedPoint
from .worker import WorkerResult


_METRIC_TYPES = {
    "logical_error": pa.bool_(),
    "default_logical_error": pa.bool_(),
    "better_weight_by_color_correlated_decoding": pa.uint8(),
    "effect_by_color_correlated_decoding": pa.uint8(),
    "color_correlated_run": pa.uint8(),
    "relift_run": pa.uint8(),
    "swim_distance": pa.float64(),
    "logical_gap": pa.float64(),
}
_PAIRED = ("logical_error", "default_logical_error",
           "better_weight_by_color_correlated_decoding",
           "effect_by_color_correlated_decoding")
_CORRELATED = (*_PAIRED, "color_correlated_run")
_RELIFTING = (*_PAIRED, "relift_run")


def _schema(names: tuple[str, ...]) -> pa.Schema:
    return pa.schema([pa.field("shot_index", pa.int64(), nullable=False)] +
                     [pa.field(name, _METRIC_TYPES[name], nullable=False) for name in names])


def _check_table(table: pa.Table, schema: pa.Schema, start: int) -> None:
    if not table.schema.equals(schema, check_metadata=False) or any(column.null_count for column in table.columns):
        raise ValueError("temporary part has incorrect schema or nulls")
    index = table.column("shot_index").to_numpy()
    if not np.array_equal(index, np.arange(start, start + len(table), dtype=np.int64)):
        raise ValueError("temporary part has invalid shot indices")
    if set(_PAIRED).issubset(schema.names):
        logical = table.column("logical_error").to_numpy()
        default = table.column("default_logical_error").to_numpy()
        effect = table.column("effect_by_color_correlated_decoding").to_numpy()
        better = table.column("better_weight_by_color_correlated_decoding").to_numpy()
        if (not np.array_equal(effect, (default & ~logical).astype(np.uint8))
                or np.any(better > 1)):
            raise ValueError("paired decoder metrics are inconsistent")
    if "color_correlated_run" in schema.names and np.any(table.column("color_correlated_run").to_numpy() > 2):
        raise ValueError("correlated run class is inconsistent")
    if "relift_run" in schema.names and np.any(table.column("relift_run").to_numpy() > 2):
        raise ValueError("relift run class is inconsistent")
    for name in ("swim_distance", "logical_gap"):
        if name in schema.names:
            values = table.column(name).to_numpy()
            if not np.isfinite(values).all() or np.any(values < 0):
                raise ValueError(f"invalid {name} values")


@dataclass(frozen=True)
class PartRecord:
    path: Path
    shot_start: int
    shot_count: int


class PointStorage:
    """Accept completed worker chunks and publish validated per-metric files.

    Create in the main process after planning. A point directory must be new.
    Waiting chunks are spooled to disk, so only one returned chunk and at most
    ``buffer_shots`` contiguous rows are held by storage at a time.
    """

    def __init__(self, point: ResolvedPoint, point_dir: Path, buffer_shots: int):
        if type(buffer_shots) is not int or buffer_shots <= 0:
            raise ValueError("buffer_shots must be a positive integer")
        self.point = point
        self.point_dir = Path(point_dir)
        if self.point_dir.name != point_directory_name(point):
            raise ValueError("point directory does not match planned name")
        self.buffer_shots = buffer_shots
        options = dict(point.color_code_options) | dict(point.decoder_options)
        base_names = (_CORRELATED if options.get("enable_colorcorrelated_decoding", False)
                      else _RELIFTING if options.get("enable_cross_color_relifting", False)
                      else _PAIRED if options.get("enable_prior_perturbation", False) or options.get("stage1_perturbation", False)
                      else ("logical_error",))
        self.names = base_names + (("swim_distance",) if dict(point.decode_options).get(
            "compute_swim_distance", False) else ()) + (("logical_gap",) if options.get(
            "comparative_decoding", False) else ())
        self.schema = _schema(self.names)
        self.point_dir.mkdir(parents=True, exist_ok=False)
        self.buffer_dir = self.point_dir / ".buffer"
        self.buffer_dir.mkdir()
        self.next_contiguous_shot = 0
        self._starts: list[int] = []
        self._ends: list[int] = []
        self._chunk_ids: set[int] = set()
        self.waiting: dict[int, Path] = {}
        self._buffer: list[pa.Table] = []
        self._buffer_rows = 0
        self._buffer_start = 0
        self.parts: list[PartRecord] = []
        self._finalized = False

    def _table(self, result: WorkerResult) -> pa.Table:
        if set(result.metrics) != set(self.names):
            raise ValueError("worker metric names do not match point")
        columns = {"shot_index": pa.array(np.arange(result.shot_start,
                         result.shot_start + result.shot_count, dtype=np.int64))}
        for name in self.names:
            values = result.metrics[name]
            dtype = (np.dtype("bool") if pa.types.is_boolean(_METRIC_TYPES[name]) else
                     np.dtype("float64") if pa.types.is_floating(_METRIC_TYPES[name]) else
                     np.dtype("uint8"))
            if not isinstance(values, np.ndarray) or values.ndim != 1 or len(values) != result.shot_count or values.dtype != dtype:
                raise ValueError(f"invalid worker metric dtype or shape: {name}")
            columns[name] = pa.array(values, type=_METRIC_TYPES[name])
        table = pa.table(columns, schema=self.schema)
        _check_table(table, self.schema, result.shot_start)
        return table

    def accept(self, result: WorkerResult) -> None:
        """Validate and spool one completion; reject any repeated or overlapping interval."""
        if self._finalized:
            raise RuntimeError("point already finalized")
        start, count = result.shot_start, result.shot_count
        if result.point_id != self.point.point_id or type(start) is not int or type(count) is not int or count <= 0 or start < 0 or start + count > self.point.shots:
            raise ValueError("invalid point identity or shot interval")
        if type(result.chunk_id) is not int or result.chunk_id < 0 or result.chunk_id in self._chunk_ids:
            raise ValueError("duplicate or invalid chunk ID")
        pos = bisect_left(self._starts, start)
        if (pos and self._ends[pos - 1] > start) or (pos < len(self._starts) and self._starts[pos] < start + count):
            raise ValueError("overlapping or duplicate shot interval")
        table = self._table(result)
        if start != self.next_contiguous_shot:
            waiting_path = self.buffer_dir / f"waiting_{start:012d}.parquet"
            if waiting_path.exists():
                raise FileExistsError(waiting_path)
            temporary = waiting_path.with_suffix(".tmp")
            pq.write_table(table, temporary)
            os.replace(temporary, waiting_path)
            self.waiting[start] = waiting_path
        self._starts.insert(pos, start)
        self._ends.insert(pos, start + count)
        self._chunk_ids.add(result.chunk_id)
        if start == self.next_contiguous_shot:
            self._append(table)
            self.next_contiguous_shot += count
            while self.next_contiguous_shot in self.waiting:
                path = self.waiting.pop(self.next_contiguous_shot)
                with pq.ParquetFile(path) as source:
                    for batch in source.iter_batches(batch_size=self.buffer_shots):
                        self._append(pa.Table.from_batches([batch]))
                self.next_contiguous_shot += pq.read_metadata(path).num_rows
                path.unlink()

    def _append(self, table: pa.Table) -> None:
        offset = 0
        while offset < len(table):
            if not self._buffer:
                self._buffer_start = int(table.column("shot_index")[offset].as_py())
            take = min(len(table) - offset, self.buffer_shots - self._buffer_rows)
            self._buffer.append(table.slice(offset, take))
            self._buffer_rows += take
            offset += take
            if self._buffer_rows == self.buffer_shots:
                self._flush()

    def _flush(self) -> None:
        if not self._buffer_rows:
            return
        table = pa.concat_tables(self._buffer)
        _check_table(table, self.schema, self._buffer_start)
        path = self.buffer_dir / f"part_{len(self.parts):06d}.parquet"
        if path.exists():
            raise FileExistsError(path)
        temporary = path.with_suffix(".tmp")
        pq.write_table(table, temporary)
        os.replace(temporary, path)
        self.parts.append(PartRecord(path, self._buffer_start, len(table)))
        self._buffer.clear()
        self._buffer_rows = 0

    def finalize(self) -> tuple[Path, ...]:
        """Stream validated parts to final files; retain the buffer on failure."""
        if self._finalized:
            raise RuntimeError("point already finalized")
        if self.next_contiguous_shot != self.point.shots or self.waiting:
            raise ValueError("point has a missing shot interval or unresolved chunks")
        self._flush()
        destinations = tuple(self.point_dir / f"{name}.parquet" for name in self.names)
        if any(path.exists() for path in destinations):
            raise FileExistsError("final metric file already exists")
        temporary = tuple(self.buffer_dir / f"final_{name}.parquet" for name in self.names)
        writers: dict[str, pq.ParquetWriter] = {}
        promoted: list[Path] = []
        try:
            for name, path in zip(self.names, temporary):
                if path.exists():
                    raise FileExistsError(path)
                writers[name] = pq.ParquetWriter(path, _schema((name,)))
            expected = 0
            for part in self.parts:
                if part.shot_start != expected:
                    raise ValueError("temporary part interval gap")
                with pq.ParquetFile(part.path) as source:
                    for batch in source.iter_batches(batch_size=self.buffer_shots):
                        table = pa.Table.from_batches([batch])
                        _check_table(table, self.schema, expected)
                        for name in self.names:
                            writers[name].write_table(table.select(["shot_index", name]))
                        expected += len(table)
                if expected != part.shot_start + part.shot_count:
                    raise ValueError("temporary part row count mismatch")
            if expected != self.point.shots:
                raise ValueError("incorrect total shot count")
            for writer in writers.values():
                writer.close()
            writers.clear()
            for name, path in zip(self.names, temporary):
                self._validate_final(path, name)
            for source, destination in zip(temporary, destinations):
                if destination.exists():
                    raise FileExistsError(destination)
                os.replace(source, destination)
                promoted.append(destination)
        except Exception:
            for writer in writers.values():
                writer.close()
            for path in promoted:
                path.unlink()
            raise
        for part in self.parts:
            part.path.unlink()
        self.buffer_dir.rmdir()
        self._finalized = True
        return destinations

    def _validate_final(self, path: Path, name: str) -> None:
        with pq.ParquetFile(path) as source:
            if source.schema_arrow != _schema((name,)) or source.metadata.num_rows != self.point.shots:
                raise ValueError(f"invalid final schema or count: {name}")
            expected = 0
            for batch in source.iter_batches(batch_size=self.buffer_shots):
                table = pa.Table.from_batches([batch])
                _check_table(table, _schema((name,)), expected)
                expected += len(table)
            if expected != self.point.shots:
                raise ValueError(f"invalid final shot indices: {name}")
