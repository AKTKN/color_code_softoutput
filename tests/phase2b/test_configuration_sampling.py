from dataclasses import replace
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
from color_code_softoutput.simulation.config import Phase2ATestConfig, batch_tasks, config_id, batch_seed
from color_code_softoutput.simulation.sampling import sample_batch, select_swim, _code_pair
from color_code_softoutput.simulation.parallel_runner import completed_batches
from color_code_softoutput.simulation.storage import SHOT_SCHEMA, write_shard, validate_shots
from color_code_softoutput.experiments.phase_2a_test import run_experiment
from color_code_softoutput.analysis.dataset import Phase2ADataset
from color_code_softoutput.analysis.audit import audit_run


@pytest.mark.parametrize('kwargs',[{'distances':(4,)},{'distances':(17,)},{'near_threshold_ps':(-.1,)},
    {'subthreshold_ps':(float('nan'),)},{'shots_per_point':0},{'num_workers':0},{'distances':(3,3)}])
def test_invalid_config(kwargs):
    with pytest.raises(ValueError): Phase2ATestConfig(**kwargs)


def small_config(**kwargs):
    return Phase2ATestConfig(distances=(3,),near_threshold_ps=(.08,),subthreshold_ps=(.04,),
                            shots_per_point=32,batch_size=16,verbose=False,**kwargs)


def test_seed_schedule():
    a = list(batch_tasks(small_config(num_workers=1),'test'))
    b = list(batch_tasks(small_config(num_workers=2),'test'))
    assert a == b
    assert len({t.seed for t in a}) == len(a)
    assert batch_seed(12,config_id(3,.04),0) == batch_seed(12,config_id(3,.04),0)


def test_selected_is_not_minimum():
    scores = np.array([[1.,9.,2.],[5.,4.,1.]])
    np.testing.assert_array_equal(select_swim(scores,np.array([1,0]),('r','g','b')),[9,5])
    np.testing.assert_array_equal(select_swim(scores[:,[2,0,1]],np.array([1,0]),('b','r','g')),[9,5])


def test_paired_once_and_alias(monkeypatch):
    task = next(batch_tasks(small_config(),'fixture'))
    ordinary,comparative = _code_pair(task.distance,task.physical_error_rate)
    calls = []
    original = ordinary.sample
    def counted(*args,**kwargs):
        result = original(*args,**kwargs)
        calls.append(result)
        return result
    monkeypatch.setattr(ordinary,'sample',counted)
    frame = sample_batch(task)
    assert len(calls) == 1 and len(frame) == task.shots
    det,obs = calls[0]
    pred,extra = comparative.decode(np.column_stack((det,obs)),full_output=True)
    np.testing.assert_array_equal(frame.forced_gap,extra['logical_gaps'])
    np.testing.assert_array_equal(frame.comparative_prediction,pred)
    records = ordinary.circuit.compile_sampler(seed=23).sample(32)
    a,b = ordinary.circuit.compile_m2d_converter().convert(measurements=records,separate_observables=True)
    c,d = comparative.circuit.compile_m2d_converter().convert(measurements=records,separate_observables=True)
    np.testing.assert_array_equal(np.column_stack((a,b)),c)
    np.testing.assert_array_equal(b,d)
    c[:,-1] ^= True
    changed,more = comparative.decode(c,full_output=True)
    c[:,-1] ^= True
    unchanged,less = comparative.decode(c,full_output=True)
    np.testing.assert_array_equal(changed,unchanged)
    np.testing.assert_array_equal(more['logical_gaps'],less['logical_gaps'])


def test_arrow_roundtrip_and_invalid_alias(tmp_path):
    frame = sample_batch(next(batch_tasks(small_config(),'fixture')))
    path = tmp_path/'part.parquet'
    write_shard(frame,path,'abc')
    table = pq.read_table(path)
    assert table.schema.equals(SHOT_SCHEMA,check_metadata=False)
    assert table.schema.metadata[b'config_hash'] == b'abc'
    assert table.to_pandas().ordinary_logical_error.dtype == bool
    pd.testing.assert_frame_equal(table.to_pandas().sort_index(axis=1),frame.sort_index(axis=1),check_dtype=False)
    with pytest.raises(FileExistsError): write_shard(frame,path,'abc')
    frame.loc[0,'forced_gap'] += 1
    with pytest.raises(ValueError,match='forced_gap'): validate_shots(frame)


def test_serial_parallel_equal():
    tasks = list(batch_tasks(small_config(),'fixture'))
    serial = pd.concat([r for _,r in completed_batches(tasks,1)])
    parallel = pd.concat([r for _,r in completed_batches(tasks,2)])
    keys = ['config_id','batch_id','shot_index']
    pd.testing.assert_frame_equal(serial.sort_values(keys).reset_index(drop=True),parallel.sort_values(keys).reset_index(drop=True))


def test_full_small_run_audit(tmp_path):
    result = run_experiment(small_config(output_root=tmp_path,num_workers=1))
    dataset = Phase2ADataset(result.run_directory)
    assert result.shots == 64
    assert audit_run(dataset)['shots'] == 64
    assert set(dataset.metric_rows('forced_gap').columns) >= {'comparative_logical_error'}
    assert 'ordinary_logical_error' not in dataset.metric_rows('forced_gap')
    metadata = json.loads((result.run_directory/'metadata.json').read_text())
    assert metadata['swim_bound_certified'] is False
    import subprocess
    repository = Path(__file__).resolve().parents[2] / 'external_libs' / 'PyMatching'
    expected_sha = subprocess.check_output(
        ['git', '-C', str(repository), 'rev-parse', 'HEAD'], text=True).strip()
    assert metadata['repositories']['PyMatching']['sha'] == expected_sha


def test_schema_linkage_and_source_archive(tmp_path):
    import hashlib
    import zipfile
    result = run_experiment(small_config(output_root=tmp_path,num_workers=1))
    dataset = Phase2ADataset(result.run_directory)
    with zipfile.ZipFile(result.run_directory/'source_snapshot.zip') as archive:
        for name,digest in dataset.metadata['source_hashes'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
    path = dataset.shards[0]
    table = pq.read_table(path).replace_schema_metadata({b'config_hash':b'wrong'})
    pq.write_table(table,path)
    with pytest.raises(ValueError,match='Mismatched configuration'):
        Phase2ADataset(result.run_directory)
