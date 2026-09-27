"""Gated small closed-memory run using the shared batching/storage infrastructure."""
import argparse
from dataclasses import asdict
from datetime import datetime
import hashlib
import logging
from pathlib import Path
import sys
from time import perf_counter
import pandas as pd
from ..circuit_level.coverage import GROWTH_CONVENTION, COVERAGE_CONVENTION
from ..circuit_level.experiment import (
    CircuitLevelMemoryConfig, memory_batch_tasks, memory_code_pair, sample_memory_batch,
    CIRCUIT_SHOT_SCHEMA, validate_memory_shots, NOISE_MODEL_NAME,
)
from ..simulation.config import PROJECT_ROOT, FORCED_GAP_SOURCE
from ..simulation.parallel_runner import completed_batches
from ..simulation.provenance import environment_metadata, write_json, archive_sources
from ..simulation.storage import write_shard
from ..simulation.pairing import validate_pairing
from .phase_2a_test import RunResult


def _static_metadata(config, directory):
    records, models = [], {}
    for d in config.distances:
        ordinary, comparative, decoder = memory_code_pair(d, config.physical_error_rate)
        records.extend(decoder.diagnostics())
        stem = directory / 'models' / f'd{d}'
        paths = {}
        for label, content in (('physical.stim',str(ordinary.circuit)),
                               ('comparative.stim',str(comparative.circuit)),
                               ('effective.dem',str(ordinary.dem_manager.dem_xz))):
            path = stem.with_name(stem.name+'_'+label)
            path.write_text(content)
            paths[path.name] = hashlib.sha256(content.encode()).hexdigest()
        for c, backend in decoder.backends.items():
            path = stem.with_name(stem.name+f'_{c}_stage2.json')
            write_json(path, asdict(backend.graph))
            paths[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        models[str(d)] = dict(files=paths, physical_detectors=ordinary.circuit.num_detectors,
            measured_observable='Z', temporal_boundary='fully terminated preparation and final readout',
            cnot_schedule=list(ordinary.cnot_schedule),
            uniform_noise_resolved=dict(ordinary.noise_model.items()),
            perfect_logical_initialization=ordinary.perfect_logical_initialization,
            perfect_logical_measurement=ordinary.perfect_logical_measurement,
            perfect_first_syndrome_extraction=ordinary.perfect_first_syndrome_extraction,
            pairing=validate_pairing(ordinary.circuit,comparative.circuit))
    return records, models


def run_experiment(config: CircuitLevelMemoryConfig, *, analyze: bool = False) -> RunResult:
    """Save one small d-round uniform-noise validation run with paired physical shots.

    Args:
        config: Explicit bounded grid/infrastructure settings.
        analyze: Run the shared three plot families after a successful raw-data audit.
    Returns:
        Shared RunResult with directory, exact shot/batch counts and sampling seconds.
    Raises:
        FileExistsError: Timestamp collision; completed runs are never overwritten.
        Exception: A gate/worker/storage failure; status and completed shards survive.
    Notes:
        Includes all-shot hard invariance checks. No threshold sweep, open boundary,
        certified-dual interpretation or minimum-over-colors aggregation is enabled.
    """
    timestamp = datetime.now().astimezone()
    experiment_id = timestamp.strftime('%Y%m%d_%H%M%S_%f_circuit_level_memory_test')
    directory = config.output_root / experiment_id
    directory.mkdir(parents=True,exist_ok=False)
    for name in ('shots','figures','logs','models'):
        (directory/name).mkdir()
    manifest = dict(environment_metadata(), timestamp=timestamp.isoformat(), timezone=str(timestamp.tzinfo),
        experiment_name='circuit_level_memory_test', config_hash=config.config_hash,
        resolved_config=config.resolved(), command_argv=sys.argv, rounds_rule='rounds = distance',
        distances=config.distances, physical_error_rates=[config.physical_error_rate],
        shots_per_point=config.shots_per_point,batch_size=config.batch_size,num_workers=config.num_workers,
        master_seed=config.master_seed,
        seed_recipe='uint64 SeedSequence([master_seed, *little_endian_uint32(SHA256(config_id)), batch_id])',
        noise_model_name=NOISE_MODEL_NAME,
        noise_model_constructor=f'NoiseModel.uniform_circuit_noise({config.physical_error_rate!r})',
        probability_role='implementation-validation point; not paper reproduction or threshold sweep',
        circuit_type='tri',cnot_schedule='tri_optimal',closed_temporal_boundary=True,sliding_window=False,
        dem_conversion=dict(path='DemManager._generate_dem -> separate_depolarizing_errors(circuit) -> detector_error_model(flatten_loops=True)',
            options={'flatten_loops':True,'other_options':'Stim defaults'},
            decomposition='actual DemDecomp H1/H2, probability sort and error-map matrices',
            remove_non_edge_like_errors=True, probability_cutoff=1e-15,
            limitations='X/Z separation drops intersector correlations; actual pre-stage1 graphlike filtering differs from paper Algorithm 1'),
        decoder_mode='ordinary concatenated MWPM, frozen-matrix replay for growth, paired existing comparative',
        selected_swim_rule='phi of unchanged ordinary hard decoder selected color; never min over colors',
        forced_gap_source=FORCED_GAP_SOURCE,
        metric_failure_labels={'selected_swim_distance':'ordinary_logical_error','forced_gap':'comparative_logical_error'},
        swim_growth_convention=GROWTH_CONVENTION,swim_coverage_convention=COVERAGE_CONVENTION,
        swim_bound_certified=False,confidence_level=.99,
        weight_tolerance={'absolute':1e-9,'relative':1e-10,'hard_invariance':'exact equality'},
        limitations='No optimal odd-cut certificate, posterior calibration, family-wide balance theorem, or sliding-window support',
        status='preprocessing',completed_shots=0,completed_batches=0)
    note = PROJECT_ROOT/'notes/support/circuit_level_swim_algorithm.tex'
    manifest['algorithm_note_sha256'] = hashlib.sha256(note.read_bytes()).hexdigest()
    additional = [note, PROJECT_ROOT/'notes/support/circuit_level_theory.tex',
                  PROJECT_ROOT/'prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md']
    additional += list((PROJECT_ROOT/'tests/circuit_level').glob('*.py'))
    notebook = PROJECT_ROOT/'notebooks/circuit_level_getting_started.ipynb'
    if notebook.exists():
        additional.append(notebook)
    for path in additional:
        manifest['source_hashes'][str(path.relative_to(PROJECT_ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    archive_sources(directory/'source_snapshot.zip',manifest['source_hashes'])
    write_json(directory/'resolved_config.json',config.resolved())
    write_json(directory/'metadata.json',manifest)
    logger = logging.getLogger(f'color_code_softoutput.{experiment_id}')
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handlers = [logging.FileHandler(directory/'logs/run.log')]
    if config.verbose:
        handlers.append(logging.StreamHandler())
    for handler in handlers:
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        logger.addHandler(handler)
    start = perf_counter()
    done = batches = 0
    try:
        diagnostics, models = _static_metadata(config,directory)
        manifest.update(static_topology=diagnostics,models=models,setup_seconds=perf_counter()-start,status='running')
        write_json(directory/'metadata.json',manifest)
        sample_start = perf_counter()
        summaries = {}
        for task, frame in completed_batches(memory_batch_tasks(config,experiment_id),config.num_workers,worker=sample_memory_batch):
            if len(frame) != task.shots:
                raise ValueError('Worker returned wrong shot count')
            write_shard(frame,directory/'shots'/f'{task.config_id}_batch{task.batch_id:06d}.parquet',
                        config.config_hash,schema=CIRCUIT_SHOT_SCHEMA,validator=validate_memory_shots)
            point = summaries.setdefault(task.config_id,dict(config_id=task.config_id,distance=task.distance,
                rounds=task.distance,physical_error_rate=task.physical_error_rate,shots=0,
                ordinary_failures=0,comparative_failures=0,hard_disagreements=0))
            point['shots'] += len(frame)
            for name in ('ordinary','comparative'):
                point[f'{name}_failures'] += int(frame[f'{name}_logical_error'].sum())
            point['hard_disagreements'] += int((frame.ordinary_prediction != frame.comparative_prediction).sum())
            done += len(frame)
            batches += 1
            logger.info('shots %d/%d; batches %d; %s; elapsed %.2fs',done,
                        len(config.distances)*config.shots_per_point,batches,task.config_id,perf_counter()-sample_start)
        pd.DataFrame(summaries.values()).sort_values('distance').to_parquet(directory/'summary.parquet',index=False)
        manifest.update(status='sampling_complete',completed_shots=done,completed_batches=batches,
            elapsed_seconds=perf_counter()-sample_start,total_seconds=perf_counter()-start,
            hard_output_invariance={'checked_shots':done,'mismatches':0,'scope':'prediction, ordinary weight, selected color, correction and failure label'},
            method_branch_shots={method:sum(config.shots_per_point for r in diagnostics if r['method']==method)
                                 for method in ('two_boundary','logical_cover')})
        write_json(directory/'metadata.json',manifest)
        from ..analysis.circuit_level import CircuitLevelDataset, audit_memory_run, standard_memory_analysis
        dataset = CircuitLevelDataset(directory)
        audit_memory_run(dataset,replay=True)
        if analyze:
            standard_memory_analysis(dataset)
        return RunResult(directory,done,batches,manifest['elapsed_seconds'])
    except BaseException as exc:
        manifest.update(status='failed',failure=repr(exc),completed_shots=done,completed_batches=batches,
                        total_seconds=perf_counter()-start)
        write_json(directory/'metadata.json',manifest)
        raise
    finally:
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()


def main() -> None:
    """Parse small-run shot/process/seed options and print RunResult.

    Returns: None. Invalid arguments exit through argparse. The d=3,5,7, p=.003
        grid stays fixed; --smoke defaults to 24 shots/point, otherwise 2000.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shots',type=int)
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--batch-size',type=int,default=250)
    parser.add_argument('--seed',type=int,default=20260916)
    parser.add_argument('--output-root',type=Path,default=CircuitLevelMemoryConfig().output_root)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--quiet',action='store_true')
    parser.add_argument('--analyze',action='store_true')
    args = parser.parse_args()
    config = CircuitLevelMemoryConfig(shots_per_point=args.shots if args.shots is not None else (24 if args.smoke else 2000),
        num_workers=args.workers,batch_size=args.batch_size,master_seed=args.seed,output_root=args.output_root,verbose=not args.quiet)
    print(run_experiment(config,analyze=args.analyze))


if __name__ == '__main__':
    main()
