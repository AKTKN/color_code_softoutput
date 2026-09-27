"""Circuit memory dataset/audit with the existing shared confidence plotters."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .dataset import Phase2ADataset
from ..circuit_level.experiment import (CircuitLevelMemoryConfig, CIRCUIT_SHOT_SCHEMA,
    memory_batch_tasks, sample_memory_batch, validate_memory_shots, memory_code_pair,
    sample_comparative_candidate_batch, COMPARATIVE_CANDIDATE_SCHEMA,
    validate_comparative_candidate_shots)
from ..simulation.config import PROJECT_ROOT
from ..simulation.parallel_runner import completed_batches
from ..simulation.provenance import write_json, repository_state
from ..simulation.storage import write_shard


class CircuitLevelDataset(Phase2ADataset):
    """Read circuit shards using the shared projected Parquet dataset interface.

    Args: run_directory: Completed or inspectable memory result directory.
    Raises: ValueError: Schema/config hash or experiment type is incompatible.
    Notes: metric_rows preserves ordinary/comparative failure-label association.
    """
    def __init__(self, run_directory: Path) -> None:
        super().__init__(run_directory,shot_schema=CIRCUIT_SHOT_SCHEMA)
        if self.metadata.get('experiment_name') != 'circuit_level_memory_test':
            raise ValueError('Expected circuit-level memory dataset')


def comparative_candidate_rows(dataset: CircuitLevelDataset, *, generate: bool = True,
                               num_workers: int | None = None) -> pd.DataFrame:
    """Load or deterministically backfill all six comparative candidate weights.

    Args:
        dataset: Completed circuit-level run whose physical shots define the sample.
        generate: Create missing sidecar shards by exact seeded replay when true.
        num_workers: Optional positive worker count; defaults to the saved run setting.
    Returns:
        One row per saved physical shot with weights for logical classes 0/1 and rgb.
    Raises:
        FileNotFoundError: Sidecars are absent and generation is disabled.
        ValueError: A sidecar, shot identity, reconstructed prediction, or gap disagrees.
    Notes:
        Sidecars live below ``comparative_candidates/`` and never rewrite raw shots.
    """
    config = CircuitLevelMemoryConfig(**dataset.metadata['resolved_config'])
    workers = config.num_workers if num_workers is None else num_workers
    if type(workers) is not int or workers < 1:
        raise ValueError("num_workers must be a positive integer")
    tasks = list(memory_batch_tasks(config, dataset.run_directory.name))
    directory = dataset.run_directory / 'comparative_candidates'
    paths = {((task.config_id, task.batch_id)):
             directory / f'{task.config_id}_batch{task.batch_id:06d}.parquet' for task in tasks}
    missing = [task for task in tasks if not paths[(task.config_id, task.batch_id)].exists()]
    if missing and not generate:
        raise FileNotFoundError(f"Missing {len(missing)} comparative candidate sidecar shards")
    if missing:
        directory.mkdir(exist_ok=True)
        for task, frame in completed_batches(missing, workers, worker=sample_comparative_candidate_batch):
            write_shard(frame, paths[(task.config_id, task.batch_id)], dataset.metadata['config_hash'],
                        schema=COMPARATIVE_CANDIDATE_SCHEMA,
                        validator=validate_comparative_candidate_shots)
    frames = []
    for task in tasks:
        path = paths[(task.config_id, task.batch_id)]
        frame = pd.read_parquet(path)
        validate_comparative_candidate_shots(frame)
        if len(frame) != task.shots:
            raise ValueError("Wrong comparative candidate batch length")
        schema = pq.read_schema(path)
        if (not schema.equals(COMPARATIVE_CANDIDATE_SCHEMA, check_metadata=False)
                or (schema.metadata or {}).get(b'config_hash', b'').decode() != dataset.metadata['config_hash']):
            raise ValueError("Incompatible comparative candidate sidecar schema/configuration")
        frames.append(frame)
    candidates = pd.concat(frames, ignore_index=True)
    base = dataset.read(columns=['config_id', 'batch_id', 'shot_index',
                                 'comparative_prediction', 'forced_gap'])
    keys = ['config_id', 'batch_id', 'shot_index']
    checked = base.merge(candidates[keys + ['baseline_logical_class', 'forced_gap']],
                         on=keys, how='outer', validate='one_to_one',
                         suffixes=('_saved', '_reconstructed'), indicator=True)
    if not checked['_merge'].eq('both').all():
        raise ValueError("Comparative sidecar and raw-shot identities differ")
    if not np.array_equal(checked.comparative_prediction, checked.baseline_logical_class):
        raise ValueError("Reconstructed comparative prediction differs from saved output")
    np.testing.assert_allclose(checked.forced_gap_saved, checked.forced_gap_reconstructed,
                               rtol=0, atol=1e-12)
    return candidates


def comparative_correction_color_summary(dataset: CircuitLevelDataset, *, generate: bool = True,
                                         num_workers: int | None = None) -> pd.DataFrame:
    """Count same/different source colors for baseline and forced corrections.

    The baseline is the decoder-selected minimum logical class; forced is its
    complementary class.  The output includes one overall row and one row per distance.
    """
    rows = comparative_candidate_rows(dataset, generate=generate, num_workers=num_workers)
    rows = rows.assign(same_color=rows.baseline_color.eq(rows.forced_color))
    groups = [('all', rows), *((str(distance), group) for distance, group in rows.groupby('distance', sort=True))]
    summary = []
    for label, group in groups:
        same = int(group.same_color.sum())
        total = len(group)
        summary.append(dict(distance=label, shots=total, same_color_count=same,
                            same_color_fraction=same / total,
                            different_color_count=total - same,
                            different_color_fraction=(total - same) / total))
    result = pd.DataFrame(summary)
    result.to_parquet(dataset.run_directory / 'comparative_correction_color_summary.parquet', index=False)
    return result


def audit_memory_run(dataset: CircuitLevelDataset, *, replay: bool = True, check_current_sources: bool = True) -> dict:
    """Recount every saved batch, verify provenance, optionally replay one batch/d.

    Args:
        dataset: CircuitLevelDataset with complete expected grid.
        replay: Reproduce full saved batches using exact original seeds and sizes.
        check_current_sources: Compare present main source hashes/external states.
    Returns:
        Audit record, also atomically saved as audit.json, with counts and replay IDs.
    Raises:
        ValueError/AssertionError: Any raw row, summary, source or replay differs.
    Notes: Replays verify saved physical shots, not additional statistical samples.
    """
    config = CircuitLevelMemoryConfig(**dataset.metadata['resolved_config'])
    tasks = {(t.config_id,t.batch_id):t for t in memory_batch_tasks(config,dataset.run_directory.name)}
    seen, counts, replayed, replay_distances = set(), {}, [], set()
    diagnostics = {(r['distance'],r['color']):r for r in dataset.metadata['static_topology']}
    for shard in dataset.shards:
        frame = pd.read_parquet(shard)
        validate_memory_shots(frame)
        ids = frame[['config_id','batch_id']].drop_duplicates()
        if len(ids) != 1:
            raise ValueError('Mixed batch identities')
        key = tuple(ids.iloc[0])
        if key in seen or key not in tasks:
            raise ValueError('Unexpected/duplicate batch')
        seen.add(key)
        task = tasks[key]
        if len(frame) != task.shots:
            raise ValueError('Wrong saved batch length')
        np.testing.assert_array_equal(frame.shot_index,np.arange(task.offset,task.offset+task.shots))
        for name,value in (('distance',task.distance),('physical_error_rate',task.physical_error_rate),
                           ('batch_seed',task.seed),('experiment_id',task.experiment_id)):
            if not (frame[name] == value).all():
                raise ValueError(f'Wrong stored task identity: {name}')
        for c in 'rgb':
            record = diagnostics[(task.distance,c)]
            for name,key2 in (('swim_method','method'),('balance_passed','balance_passed'),('class_exists','class_exists')):
                if not (frame[f'{name}_{c}'] == record[key2]).all():
                    raise ValueError('Stored topology flags disagree with frozen graph')
        point = counts.setdefault(task.config_id,dict(config_id=task.config_id,distance=task.distance,rounds=task.distance,
            physical_error_rate=task.physical_error_rate,shots=0,ordinary_failures=0,comparative_failures=0,hard_disagreements=0))
        point['shots'] += len(frame)
        for decoder in ('ordinary','comparative'):
            point[f'{decoder}_failures'] += int(np.count_nonzero(frame[f'{decoder}_prediction'] != frame.actual_observable))
        point['hard_disagreements'] += int(np.count_nonzero(frame.ordinary_prediction != frame.comparative_prediction))
        if replay and task.distance not in replay_distances:
            repeated = sample_memory_batch(task)
            pd.testing.assert_frame_equal(frame.sort_index(axis=1),repeated.sort_index(axis=1),check_dtype=False)
            replay_distances.add(task.distance)
            replayed.append(asdict(task))
    if seen != set(tasks):
        raise ValueError('Incomplete memory run')
    summary = pd.DataFrame(counts.values()).sort_values('distance').reset_index(drop=True)
    saved = pd.read_parquet(dataset.run_directory/'summary.parquet').sort_values('distance').reset_index(drop=True)
    pd.testing.assert_frame_equal(summary[saved.columns],saved,check_dtype=False)
    if (int(summary.shots.sum()) != dataset.metadata['completed_shots']
            or len(seen) != dataset.metadata['completed_batches']
            or dataset.metadata['hard_output_invariance']['checked_shots'] != int(summary.shots.sum())
            or dataset.metadata['hard_output_invariance']['mismatches'] != 0):
        raise ValueError('Manifest shot counts or hard invariance disagree with saved data')
    with zipfile.ZipFile(dataset.run_directory/'source_snapshot.zip') as archive:
        for name,digest in dataset.metadata['source_hashes'].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError(f'Archived source mismatch: {name}')
            if check_current_sources and hashlib.sha256((PROJECT_ROOT/name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Current source mismatch: {name}')
    for model in dataset.metadata['models'].values():
        for name,digest in model['files'].items():
            if hashlib.sha256((dataset.run_directory/'models'/name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Frozen model mismatch: {name}')
    if check_current_sources:
        for name in ('PyMatching','color-code-stim'):
            if repository_state(PROJECT_ROOT/'external_libs'/name) != dataset.metadata['repositories'][name]:
                raise ValueError(f'External repository changed: {name}')
    result = dict(status='passed',shots=int(summary.shots.sum()),shards=len(seen),replayed_batches=replayed,
                  current_sources_checked=check_current_sources,source_archive_verified=True,
                  hard_output_invariance=dataset.metadata['hard_output_invariance'],
                  ordinary_failures=int(summary.ordinary_failures.sum()),
                  comparative_failures=int(summary.comparative_failures.sum()),
                  hard_disagreements=int(summary.hard_disagreements.sum()))
    write_json(dataset.run_directory/'audit.json',result)
    return result


def inspect_memory_witnesses(dataset: CircuitLevelDataset, *, max_shots: int = 3) -> list[dict]:
    """Replay saved batches and return verified per-color witness examples.

    Args:
        dataset: Saved memory dataset; no new independently sampled shots are added.
        max_shots: Positive maximum; prioritize ordinary/comparative disagreements.
    Returns:
        JSON-ready shot IDs, scores and original mechanism supports with stable IDs,
        saved also in witness_examples.json. Residuals are natural-log costs.
    Raises: ValueError: Invalid count or a replay does not match saved predictions.
    """
    if type(max_shots) is not int or max_shots < 1:
        raise ValueError('Positive witness example count required')
    config = CircuitLevelMemoryConfig(**dataset.metadata['resolved_config'])
    tasks = {(t.config_id,t.batch_id):t for t in memory_batch_tasks(config,dataset.run_directory.name)}
    frame = dataset.read()
    frame['disagreement'] = frame.ordinary_prediction != frame.comparative_prediction
    examples = frame.sort_values(['disagreement','ordinary_logical_error'],ascending=False).head(max_shots)
    result = []
    for key, selected in examples.groupby(['config_id','batch_id']):
        task = tasks[key]
        code, _, decoder = memory_code_pair(task.distance,task.physical_error_rate)
        det, actual = code.sample(task.shots,seed=task.seed)
        local = (selected.shot_index-task.offset).to_numpy()
        pred, extra = decoder.decode(det[local],return_witness=True)
        if not np.array_equal(pred,selected.ordinary_prediction) or not np.array_equal(actual[local],selected.actual_observable):
            raise ValueError('Witness replay differs from stored physical shots')
        np.testing.assert_array_equal(extra['swim_distances_by_color'],
                                      selected[[f'swim_distance_{c}' for c in 'rgb']].to_numpy())
        for i, (_, row) in enumerate(selected.iterrows()):
            result.append(dict(config_id=task.config_id,shot_index=int(row.shot_index),
                ordinary_failure=bool(row.ordinary_logical_error),disagreement=bool(row.disagreement),
                selected_color=row.ordinary_selected_color,
                branches={c:dict(phi=float(extra['swim_distances_by_color'][i,j]),
                    **asdict(extra['witnesses_by_color'][c][i])) for j,c in enumerate('rgb')}))
    write_json(dataset.run_directory/'witness_examples.json',{'examples':result})
    return result


def standard_memory_analysis(dataset: CircuitLevelDataset, *, style=None, round_digits: int | None = None) -> dict:
    """Generate the existing distribution, conditional-LER and paired retention plots.

    Args:
        dataset: Saved validated memory run.
        style: Shared RevtexFigureStyle, or default publication style.
        round_digits: Optional rounding of actual scores in all three plots.
    Returns:
        Counts of plot families/tables; figures are saved as PDF/PNG and closed.
    Raises: ValueError/RuntimeError: Invalid data or unavailable plotting dependencies.
    """
    import matplotlib.pyplot as plt
    from .swim_distribution import SwimDistanceDistributionPlotter
    from .conditional_ler import ConditionalLERAnalyzer
    from .postselection import PostSelectionAnalyzer
    values = dataset.available_values()
    selection = dict(distance=values['distance'],physical_error_rate=values['physical_error_rate'][0])
    suffix = "" if round_digits is None else f"_round{round_digits}"
    figure, counts = SwimDistanceDistributionPlotter(style).plot(dataset,**selection,round_digits=round_digits)
    counts.to_parquet(dataset.run_directory/f'swim_distribution_counts{suffix}.parquet',index=False)
    plt.close(figure)
    figure, rates, fits = ConditionalLERAnalyzer(style).plot(dataset,**selection,overlay_fit=False,round_digits=round_digits)
    rates.to_parquet(dataset.run_directory/f'conditional_ler_counts{suffix}.parquet',index=False)
    plt.close(figure)
    figure, retention = PostSelectionAnalyzer(style).plot(dataset,**selection,include_forced_gap=True,round_digits=round_digits)
    plt.close(figure)
    return dict(plot_families=3,distribution_rows=len(counts),conditional_rows=len(rates),retention_rows=len(retention))
