"""Synthetic storage tests; no circuit sampling or runner is involved."""

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.simulation.planner import point_directory_name
from color_code_softoutput.simulation.task import ResolvedPoint
from color_code_softoutput.simulation.worker import WorkerResult
from color_code_softoutput.simulation.workflow_storage import PointStorage


def _point(correlated=False, shots=13):
    return ResolvedPoint("point", "concat", 3, .01, "bitflip", 1, "tri",
                         "tri_optimal", shots, (),
                         (("enable_colorcorrelated_decoding", correlated),), ())


def _result(start, count, *, correlated=False, chunk_id=None):
    logical = (np.arange(start, start + count) % 3 == 0)
    metrics = {"logical_error": logical}
    if correlated:
        default = (np.arange(start, start + count) % 2 == 0)
        metrics.update(default_logical_error=default,
                       better_weight_by_color_correlated_decoding=np.ones(count, dtype=np.uint8),
                       effect_by_color_correlated_decoding=(default & ~logical).astype(np.uint8),
                       color_correlated_run=(np.arange(start, start + count) % 3).astype(np.uint8))
    return WorkerResult("point", start if chunk_id is None else chunk_id,
                        start, count, .01, metrics)


@pytest.mark.parametrize("order", [(0, 1, 2, 3), (3, 2, 1, 0), (2, 0, 3, 1)])
@pytest.mark.parametrize("correlated", [False, True])
def test_scrambled_chunks_exact_schema_and_cleanup(tmp_path, order, correlated):
    point = _point(correlated)
    store = PointStorage(point, tmp_path / point_directory_name(point), 3)
    chunks = [(0, 2), (2, 4), (6, 3), (9, 4)]
    for i in order:
        start, count = chunks[i]
        store.accept(_result(start, count, correlated=correlated))
    assert len(store.parts) >= 4
    temporary_schema = pq.read_schema(store.parts[0].path)
    assert temporary_schema == pa.schema(
        [pa.field("shot_index", pa.int64(), nullable=False)] +
        [pa.field(name, pa.bool_() if name.endswith("logical_error") else pa.uint8(), nullable=False)
         for name in store.names])
    outputs = store.finalize()
    assert not store.buffer_dir.exists()
    assert len(outputs) == (5 if correlated else 1)
    assert sorted(p.name for p in store.point_dir.iterdir()) == sorted(p.name for p in outputs)
    for path in outputs:
        table = pq.read_table(path)
        metric = path.stem
        assert table.schema == pa.schema([pa.field("shot_index", pa.int64(), nullable=False),
                                          pa.field(metric, pa.bool_() if metric.endswith("logical_error") else pa.uint8(), nullable=False)])
        assert table.num_rows == point.shots
        assert table.column_names == ["shot_index", metric]
        assert table.column("shot_index").to_pylist() == list(range(point.shots))
        assert all(column.null_count == 0 for column in table.columns)
    if correlated:
        columns = {path.stem: pq.read_table(path).column(path.stem).to_numpy() for path in outputs}
        assert np.array_equal(columns["effect_by_color_correlated_decoding"],
                              (columns["default_logical_error"] & ~columns["logical_error"]).astype(np.uint8))


def test_reject_overlap_duplicate_and_gap(tmp_path):
    point = _point(shots=6)
    store = PointStorage(point, tmp_path / point_directory_name(point), 2)
    store.accept(_result(0, 2))
    with pytest.raises(ValueError, match="overlapping|duplicate"):
        store.accept(_result(1, 2))
    with pytest.raises(ValueError, match="duplicate"):
        store.accept(_result(2, 2, chunk_id=0))
    store.accept(_result(4, 2))
    with pytest.raises(ValueError, match="missing shot interval"):
        store.finalize()
    assert store.buffer_dir.exists()
    store.accept(_result(2, 2))
    store.finalize()


def test_bad_metric_and_effect_rejected(tmp_path):
    point = _point(True, shots=2)
    store = PointStorage(point, tmp_path / point_directory_name(point), 2)
    bad = _result(0, 2, correlated=True)
    bad.metrics["logical_error"] = bad.metrics["logical_error"].astype(np.uint8)
    with pytest.raises(ValueError, match="dtype"):
        store.accept(bad)
    bad = _result(0, 2, correlated=True)
    bad.metrics["effect_by_color_correlated_decoding"][:] = 1
    with pytest.raises(ValueError, match="inconsistent"):
        store.accept(bad)
    bad = _result(0, 2, correlated=True)
    bad.metrics["color_correlated_run"][0] = 3
    with pytest.raises(ValueError, match="inconsistent"):
        store.accept(bad)


def test_relift_run_sidecar_uses_existing_shot_schema(tmp_path):
    point = ResolvedPoint("point", "relifting", 3, .01, "bitflip", 1, "tri",
                          "tri_optimal", 3, (), (("enable_cross_color_relifting", True),), ())
    store = PointStorage(point, tmp_path / point_directory_name(point), 2)
    default = np.array([False, True, True])
    logical = np.array([False, True, False])
    result = WorkerResult("point", 0, 0, 3, .01,
                          {"logical_error": logical,
                           "default_logical_error": default,
                           "better_weight_by_color_correlated_decoding": np.array([0, 0, 1], dtype=np.uint8),
                           "effect_by_color_correlated_decoding": (default & ~logical).astype(np.uint8),
                           "relift_run": np.array([0, 1, 2], dtype=np.uint8)})
    store.accept(result)
    paths = store.finalize()
    assert {path.name for path in paths} == {f"{name}.parquet" for name in store.names}
    table = pq.read_table(store.point_dir / "relift_run.parquet")
    assert table.schema == pa.schema([pa.field("shot_index", pa.int64(), nullable=False),
                                      pa.field("relift_run", pa.uint8(), nullable=False)])
    assert table.column("shot_index").to_pylist() == [0, 1, 2]
    assert table.column("relift_run").to_pylist() == [0, 1, 2]


def test_perturbation_paired_metric_storage(tmp_path):
    point = ResolvedPoint("point", "perturbation", 3, .01, "bitflip", 1, "tri",
                          "tri_optimal", 2, (), (("enable_prior_perturbation", True),), ())
    store = PointStorage(point, tmp_path / point_directory_name(point), 2)
    result = WorkerResult("point", 0, 0, 2, .01, {
        "logical_error": np.array([False, False]),
        "default_logical_error": np.array([True, False]),
        "better_weight_by_color_correlated_decoding": np.array([1, 0], dtype=np.uint8),
        "effect_by_color_correlated_decoding": np.array([1, 0], dtype=np.uint8),
    })
    store.accept(result)
    paths = store.finalize()
    assert {path.name for path in paths} == {f"{name}.parquet" for name in store.names}
    assert pq.read_table(store.point_dir / "default_logical_error.parquet").column(
        "default_logical_error").to_pylist() == [True, False]


def test_failure_preserves_buffer_and_no_final_names(tmp_path, monkeypatch):
    point = _point(True, shots=5)
    store = PointStorage(point, tmp_path / point_directory_name(point), 2)
    store.accept(_result(0, 5, correlated=True))
    original = store._validate_final
    calls = 0

    def fail_on_second(path, name):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected validation failure")
        return original(path, name)

    monkeypatch.setattr(store, "_validate_final", fail_on_second)
    with pytest.raises(RuntimeError, match="injected"):
        store.finalize()
    assert store.buffer_dir.exists()
    assert list(store.point_dir.glob("*.parquet")) == []


def test_failed_publication_rolls_back_final_names(tmp_path, monkeypatch):
    point = _point(True, shots=3)
    store = PointStorage(point, tmp_path / point_directory_name(point), 2)
    store.accept(_result(0, 3, correlated=True))
    from color_code_softoutput.simulation import workflow_storage
    original = workflow_storage.os.replace
    promoted = 0

    def fail_second_final(source, destination):
        nonlocal promoted
        if destination.parent == store.point_dir:
            promoted += 1
            if promoted == 2:
                raise OSError("injected rename failure")
        return original(source, destination)

    monkeypatch.setattr(workflow_storage.os, "replace", fail_second_final)
    with pytest.raises(OSError, match="injected"):
        store.finalize()
    assert store.buffer_dir.exists()
    assert list(store.point_dir.glob("*.parquet")) == []


def test_no_overwrite_and_out_of_order_spooling(tmp_path):
    point = _point(shots=8)
    path = tmp_path / point_directory_name(point)
    store = PointStorage(point, path, 2)
    store.accept(_result(4, 4))
    assert store._buffer_rows == 0
    assert len(store.waiting) == 1
    assert next(iter(store.waiting.values())).exists()
    with pytest.raises(FileExistsError):
        PointStorage(point, path, 2)
    store.accept(_result(0, 4))
    store.finalize()


def test_streams_parts_without_full_read_or_full_concat(tmp_path, monkeypatch):
    point = _point(shots=19)
    store = PointStorage(point, tmp_path / point_directory_name(point), 3)
    for start, count in [(0, 2), (2, 7), (9, 5), (14, 5)]:
        store.accept(_result(start, count))
    assert len(store.parts) > 1
    original = pq.ParquetFile.iter_batches
    observed = []

    def bounded(self, *args, **kwargs):
        observed.append(kwargs.get("batch_size"))
        yield from original(self, *args, **kwargs)

    monkeypatch.setattr(pq.ParquetFile, "iter_batches", bounded)
    store.finalize()
    assert observed and all(size == 3 for size in observed)
