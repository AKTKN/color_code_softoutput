"""Timestamped surface-memory runner with atomic shards, provenance and replay."""
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
from time import perf_counter
import zipfile
import numpy as np
import pandas as pd
from color_code_softoutput.simulation.parallel_runner import completed_batches
from color_code_softoutput.simulation.storage import write_shard
from color_code_softoutput.simulation.provenance import environment_metadata, archive_sources, write_json, repository_state
from .model import ROOT, EXAMPLE, model, GROWTH_CONVENTION, PATH_GAP_VERSION
from .simulation import SurfaceConfig, batch_tasks, sample_batch, SHOT_SCHEMA, validate_shots, NOISE_MODEL
from .analysis import SurfaceDataset, standard_analysis


def audit_run(run_directory: Path, *, replay: bool = True, check_current_sources: bool = True) -> dict:
    """Verify all raw rows, independent counts, archived models/source and saved seeds.

    Args:
        run_directory: Finished run, with one shard per deterministic batch.
        replay: Reproduce one entire saved batch per distance, using its original seed.
        check_current_sources: Require current source/externals to match the snapshot.
    Returns: Audit record, also saved atomically in audit.json.
    Raises: ValueError/AssertionError for corrupt/incomplete data or replay mismatch.
    """
    dataset = SurfaceDataset(run_directory)
    meta = dataset.metadata
    config = SurfaceConfig(**meta['resolved_config'])
    if config.config_hash != meta['config_hash']:
        raise ValueError('Manifest configuration hash mismatch')
    tasks = {(t.config_id,t.batch_id):t for t in batch_tasks(config,dataset.run_directory.name)}
    seen, records, replayed = set(), [], set()
    replay_ids = []
    for shard in dataset.shards:
        frame = pd.read_parquet(shard)
        validate_shots(frame)
        identities = frame[['config_id','batch_id']].drop_duplicates()
        if len(identities) != 1:
            raise ValueError('Mixed batch identities')
        key = tuple(identities.iloc[0])
        if key not in tasks or key in seen:
            raise ValueError('Unexpected/duplicate batch')
        seen.add(key)
        task = tasks[key]
        if len(frame) != task.shots:
            raise ValueError('Wrong shot count')
        np.testing.assert_array_equal(frame.shot_index,np.arange(task.offset,task.offset+task.shots))
        for name,value in (('experiment_id',task.experiment_id),('batch_seed',task.seed),
                           ('distance',task.distance),('rounds',task.rounds),('physical_error_rate',task.physical_error_rate)):
            if not (frame[name] == value).all():
                raise ValueError(f'Wrong batch field: {name}')
        records.append(dict(distance=task.distance,rounds=task.rounds,shots=len(frame),
                            failures=int((frame.ordinary_prediction != frame.actual_observable).sum())))
        if replay and task.distance not in replayed:
            repeated = sample_batch(task)
            pd.testing.assert_frame_equal(frame,repeated[frame.columns],check_dtype=False)
            replayed.add(task.distance)
            replay_ids.append(asdict(task))
    if seen != set(tasks):
        raise ValueError('Incomplete batch grid')
    summary = pd.DataFrame(records).groupby(['distance','rounds'],as_index=False).sum()
    saved = pd.read_parquet(dataset.run_directory/'summary.parquet')
    pd.testing.assert_frame_equal(summary,saved,check_dtype=False)
    with zipfile.ZipFile(dataset.run_directory/'source_snapshot.zip') as archive:
        for name,digest in meta['source_hashes'].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError(f'Archived source changed: {name}')
            if check_current_sources and hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Current source changed: {name}')
    for name,digest in meta['model_hashes'].items():
        if hashlib.sha256((dataset.run_directory/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Model changed: {name}')
    if check_current_sources:
        for name in ('PyMatching','color-code-stim'):
            if repository_state(ROOT/'external_libs'/name) != meta['repositories'][name]:
                raise ValueError(f'External repository changed: {name}')
    shots = int(summary.shots.sum())
    if shots != meta['completed_shots'] or len(seen) != meta['completed_batches'] or meta['hard_output_invariance'] != {'checked_shots':shots,'mismatches':0}:
        raise ValueError('Manifest counts/invariance mismatch')
    result = dict(status='passed',shots=shots,shards=len(seen),failures=int(summary.failures.sum()),
                  replayed_batches=replay_ids,source_archive_verified=True,current_sources_checked=check_current_sources,
                  hard_output_invariance=meta['hard_output_invariance'])
    write_json(dataset.run_directory/'audit.json',result)
    return result


def run_experiment(config: SurfaceConfig, *, analyze: bool = True, verbose: bool = True) -> Path:
    """Run a closed-memory paired grid using shared workers/seeds/storage/style.

    Args:
        config: SurfaceConfig; defaults are a small validation, not a paper campaign.
        analyze: Save the distribution, conditional-LER and postselection plot families after raw-data/replay checks.
        verbose: Print one progress record per completed batch.
    Returns: New timestamped run directory with full provenance and audit.
    Raises: All failed gates propagate; partial shards and failure metadata survive.
    """
    timestamp = datetime.now().astimezone()
    run = config.output_root/timestamp.strftime('%Y%m%d_%H%M%S_%f_surface_code_memory')
    run.mkdir(parents=True,exist_ok=False)
    for name in ('shots','models','figures'):
        (run/name).mkdir()
    meta = dict(environment_metadata(),experiment_name='surface_code_memory',
        timestamp=timestamp.isoformat(),timezone=str(timestamp.tzinfo),resolved_config=config.resolved(),
        config_hash=config.config_hash,noise_model_name=NOISE_MODEL,memory_basis='X',
        circuit_source='SO_example: X_init(False), SE_round(False) repeated rounds times, X_meas(False)',
        rounds_semantics='rounds = rounds_factor * distance SE_round calls; X_init includes an additional noisy extraction',
        noise_placement='Exact external Meta_Circuit: DEPOLARIZE1/2(p), preparation/readout/reset X_ERROR(p), noisy Hadamards and scheduled idle layer',
        decoding_model='SO_example.DEM.prune_post_selected -> Matching; actual merged graph saved in models',
        model_limitations='Upstream parser decomposition can drop unsupported composite mechanisms; matching does not retain all correlated physical likelihoods',
        complementary_gap_definition='abs(W1-W0): two constrained minimum matching weights in the same frozen ordinary graph',
        label_gauge='Check internal balance; force appended gauged row to logical_bit XOR detector_potential_parity',
        path_gap_metric_version=PATH_GAP_VERSION,
        path_gap_definition='D(E)-sum(original edge weights over full XOR correction E); correction edges zeroed; same split X-boundary topology as swim; signed, no radii',
        path_gap_weight_convention='Original floating edge weights; ordinary_solution_weight separately retains backend quantization',
        metric_failure_labels={name:'ordinary_logical_error' for name in ('swim_distance','complementary_gap','path_gap')},
        stored_score_units='natural-log matching costs, unrounded',display_units='dB = 10/ln(10) times stored cost, unrounded',
        swim_growth_convention=GROWTH_CONVENTION,swim_bound_certified=False,
        soft_output_api='configure_soft_output + decode_batch_with_soft_output; example spatial X-boundary topology',
        hard_weight_tolerance={'absolute':1e-8,'relative':1e-10,'SO_on_off':'exact equality'},
        seed_recipe='shared batch_seed(master_seed, surface_config_id, batch_id); independent of worker scheduling',
        postselection='retain >= each exact unique raw threshold; whole ties; zero-failure rows retained',
        closed_temporal_boundary=True,sliding_window=False,confidence_level=.99,
        status='preprocessing',completed_shots=0,completed_batches=0)
    files = list((ROOT/'surface_code_test').glob('*.py'))
    for directory in ('scripts','tests','notebooks'):
        files += [p for p in (ROOT/'surface_code_test'/directory).iterdir() if p.suffix in ('.py','.ipynb')]
    files += list(EXAMPLE.glob('*.py'))+[EXAMPLE/'readme.md']
    # Archive modified native backend sources too, since the checkout can be dirty.
    backend = ROOT/'external_libs/PyMatching/src/pymatching'
    files += [p for p in backend.rglob('*') if p.suffix in ('.py','.h','.cc')]
    for path in files:
        meta['source_hashes'][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    archive_sources(run/'source_snapshot.zip',meta['source_hashes'])
    write_json(run/'metadata.json',meta)
    write_json(run/'resolved_config.json',config.resolved())
    start = perf_counter()
    try:
        diagnostics, model_hashes = {}, {}
        for d in config.distances:
            decoder = model(d,d*config.rounds_factor,config.physical_error_rate)
            diagnostics[str(d)] = decoder.diagnostics
            circuit_file = run/'models'/f'd{d}.stim'
            circuit_file.write_text(str(decoder.circuit))
            dem_file = run/'models'/f'd{d}_physical.dem'
            dem_file.write_text(str(decoder.circuit.detector_error_model()))
            graph_file = run/'models'/f'd{d}_matching.json'
            write_json(graph_file,dict(edges=[dict(u=u,v=v,weight=data['weight'],probability=data['error_probability'],
                fault_ids=sorted(data['fault_ids'])) for u,v,data in decoder.complementary.edges],
                detector_potential=decoder.complementary.potential.tolist(),
                soft_output_topology=asdict(decoder.topology)))
            for path in (circuit_file,dem_file,graph_file):
                model_hashes[str(path.relative_to(run))] = hashlib.sha256(path.read_bytes()).hexdigest()
        meta.update(setup_seconds=perf_counter()-start,static_diagnostics=diagnostics,model_hashes=model_hashes,status='running')
        write_json(run/'metadata.json',meta)
        sample_start = perf_counter()
        records = []
        for task,frame in completed_batches(batch_tasks(config,run.name),config.num_workers,worker=sample_batch):
            write_shard(frame,run/'shots'/f'{task.config_id}_batch{task.batch_id:06d}.parquet',
                        config.config_hash,schema=SHOT_SCHEMA,validator=validate_shots)
            records.append(dict(distance=task.distance,rounds=task.rounds,shots=len(frame),failures=int(frame.ordinary_logical_error.sum())))
            meta['completed_shots'] += len(frame)
            meta['completed_batches'] += 1
            if verbose:
                print(f"{meta['completed_shots']}/{len(config.distances)*config.shots_per_point} shots; d={task.distance}; {perf_counter()-sample_start:.2f}s",flush=True)
        summary = pd.DataFrame(records).groupby(['distance','rounds'],as_index=False).sum()
        summary.to_parquet(run/'summary.parquet',index=False)
        meta.update(sampling_seconds=perf_counter()-sample_start,status='sampling_complete',
                    hard_output_invariance=dict(checked_shots=meta['completed_shots'],mismatches=0))
        write_json(run/'metadata.json',meta)
        audit_run(run,replay=True)
        if analyze:
            standard_analysis(SurfaceDataset(run))
        meta.update(status='complete',total_seconds=perf_counter()-start)
        write_json(run/'metadata.json',meta)
        return run
    except BaseException as error:
        meta.update(status='failed',failure=repr(error),total_seconds=perf_counter()-start)
        write_json(run/'metadata.json',meta)
        raise
