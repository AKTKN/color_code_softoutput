"""Shared infrastructure, physical pairing, raw data, figures and replay acceptance."""
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import pyarrow.parquet as pq
from color_code_softoutput.circuit_level.experiment import (
    CircuitLevelMemoryConfig, memory_batch_tasks, sample_memory_batch, memory_code_pair,
    CIRCUIT_SHOT_SCHEMA, validate_memory_shots, sample_comparative_candidate_batch,
    COMPARATIVE_CANDIDATE_SCHEMA, validate_comparative_candidate_shots,
)
from color_code_softoutput.experiments.circuit_level_memory_test import run_experiment
from color_code_softoutput.analysis.circuit_level import (
    CircuitLevelDataset, audit_memory_run, inspect_memory_witnesses, standard_memory_analysis,
    comparative_candidate_rows, comparative_correction_color_summary,
)
from color_code_softoutput.analysis.figure_style import RevtexFigureStyle
from color_code_softoutput.simulation.parallel_runner import completed_batches
from color_code_softoutput.simulation.storage import write_shard


def small(**kwargs):
    return CircuitLevelMemoryConfig(distances=(3,),shots_per_point=24,batch_size=12,verbose=False,**kwargs)


@pytest.mark.parametrize('kwargs', [dict(distances=(3,3)),dict(distances=(9,)),dict(physical_error_rate=0),
    dict(physical_error_rate=float('nan')),dict(shots_per_point=0),dict(num_workers=0),dict(master_seed=-1)])
def test_config_rejects_invalid(kwargs):
    with pytest.raises(ValueError):
        CircuitLevelMemoryConfig(**kwargs)


def test_shared_seed_and_parallel_runner():
    config = small(num_workers=1)
    tasks = list(memory_batch_tasks(config,'test'))
    assert tasks == list(memory_batch_tasks(replace(config,num_workers=2),'test'))
    a = pd.concat([f for _,f in completed_batches(tasks,1,worker=sample_memory_batch)])
    b = pd.concat([f for _,f in completed_batches(tasks,2,worker=sample_memory_batch)])
    keys = ['config_id','batch_id','shot_index']
    pd.testing.assert_frame_equal(a.sort_values(keys).reset_index(drop=True),b.sort_values(keys).reset_index(drop=True))


def test_sample_once_alias_and_atomic_storage(monkeypatch,tmp_path):
    task = next(memory_batch_tasks(small(),'test'))
    code, comparative, _ = memory_code_pair(task.distance,task.physical_error_rate)
    calls = []
    original = code.sample
    def record(*args,**kwargs):
        answer = original(*args,**kwargs)
        calls.append(answer)
        return answer
    monkeypatch.setattr(code,'sample',record)
    frame = sample_memory_batch(task)
    assert len(calls) == 1
    det,obs = calls[0]
    pred,extra = comparative.decode(np.column_stack((det,obs)),full_output=True)
    np.testing.assert_array_equal(pred,frame.comparative_prediction)
    np.testing.assert_array_equal(extra['logical_gaps'],frame.forced_gap)
    path = tmp_path/'part.parquet'
    write_shard(frame,path,'fixture',schema=CIRCUIT_SHOT_SCHEMA,validator=validate_memory_shots)
    assert pq.read_schema(path).equals(CIRCUIT_SHOT_SCHEMA,check_metadata=False)
    assert not path.with_suffix('.parquet.tmp').exists()
    with pytest.raises(FileExistsError):
        write_shard(frame,path,'fixture',schema=CIRCUIT_SHOT_SCHEMA,validator=validate_memory_shots)
    frame.loc[0,'swim_bound_certified'] = True
    with pytest.raises(ValueError,match='flags'):
        validate_memory_shots(frame)


def test_comparative_candidate_sidecar_reconstructs_existing_decoder():
    task = next(memory_batch_tasks(small(), 'test'))
    frame = sample_comparative_candidate_batch(task)
    validate_comparative_candidate_shots(frame)
    assert list(frame.columns) == COMPARATIVE_CANDIDATE_SCHEMA.names
    code, comparative, _ = memory_code_pair(task.distance, task.physical_error_rate)
    detectors, actual = code.sample(task.shots, seed=task.seed)
    prediction, extra = comparative.decode(np.column_stack((detectors, actual)), full_output=True)
    np.testing.assert_array_equal(frame.baseline_logical_class, prediction)
    np.testing.assert_allclose(frame.forced_gap, extra['logical_gaps'], rtol=0, atol=1e-12)
    assert (frame.forced_logical_class != frame.baseline_logical_class).all()
    assert frame.baseline_color.isin(tuple('rgb')).all()
    assert frame.forced_color.isin(tuple('rgb')).all()
    broken = frame.copy()
    broken.loc[0, 'forced_gap'] += 1
    with pytest.raises(ValueError, match='forced_gap'):
        validate_comparative_candidate_shots(broken)


@pytest.mark.parametrize("hide_prompt", [False, True])
def test_end_to_end_run_notebook_workflow_and_corrupt_schema(
    tmp_path, monkeypatch, hide_prompt,
):
    prompt = Path(__file__).resolve().parents[2] / (
        "prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md"
    )
    prompt_available = prompt.is_file() and not hide_prompt
    if hide_prompt:
        original_is_file = Path.is_file

        def without_optional_prompt(path):
            if path.name == "CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md":
                return False
            return original_is_file(path)

        monkeypatch.setattr(Path, "is_file", without_optional_prompt)
    result = run_experiment(small(output_root=tmp_path,num_workers=1))
    dataset = CircuitLevelDataset(result.run_directory)
    assert result.shots == 24
    assert audit_memory_run(dataset)['shots'] == 24
    assert len(dataset.read(rounds=3,noise_model_name='uniform_circuit_noise')) == 24
    assert len(dataset.metric_rows('forced_gap')) == 24
    examples = inspect_memory_witnesses(dataset,max_shots=2)
    assert len(examples) == 2 and all(x['branches']['r']['column_ids'] for x in examples)
    candidates = comparative_candidate_rows(dataset, num_workers=1)
    assert len(candidates) == 24
    summary = comparative_correction_color_summary(dataset, generate=False)
    assert list(summary.distance) == ['all', '3']
    assert (summary.same_color_count + summary.different_color_count == summary.shots).all()
    np.testing.assert_allclose(summary.same_color_fraction + summary.different_color_fraction, 1)
    assert (result.run_directory / 'comparative_correction_color_summary.parquet').exists()
    assert standard_memory_analysis(dataset,style=RevtexFigureStyle(test_mode=True))['plot_families'] == 3
    metadata = json.loads((result.run_directory/'metadata.json').read_text())
    prompt_key = 'prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md'
    assert (prompt_key in metadata['source_hashes']) == prompt_available
    assert metadata['method_branch_shots'] == {'two_boundary':72,'logical_cover':0}
    assert metadata['hard_output_invariance']['mismatches'] == 0
    assert metadata['models']['3']['uniform_noise_resolved']['cnot'] == .003
    path = dataset.shards[0]
    table = pq.read_table(path).replace_schema_metadata({b'config_hash':b'wrong'})
    pq.write_table(table,path)
    with pytest.raises(ValueError,match='configuration hash'):
        CircuitLevelDataset(result.run_directory)
