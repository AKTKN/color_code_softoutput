"""Same-shot benchmark of ordinary, correlated, relifted and perturbed decoding.

This is a separate v2 result format. Each metric sidecar retains the canonical
shot_index/value schema; the manifest carries the shared configuration and
batch provenance. No previous workflow result directory is reused.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from color_code_stim import ColorCode

from .noise import make_noise_model
from .worker import logical_errors
from .workflow_storage import _check_table, _schema


KINDS = ("baseline", "single_relift", "all_color_relift")
_TYPES = {
    "baseline_error": pa.bool_(), "color_correlated_error": pa.bool_(),
    "relift_error": pa.bool_(), "perturbation_error": pa.bool_(),
    "color_correlated_run": pa.uint8(), "relift_run": pa.uint8(),
    "color_correlated_extra_mwpm_calls": pa.uint8(),
    "color_correlated_selected_kind": pa.uint8(),
    "relift_extra_stage2_calls": pa.uint8(), "relift_total_mwpm_calls": pa.uint8(),
    "relift_candidate_slots": pa.uint8(), "relift_unique_stage2_syndromes": pa.uint8(),
    "relift_aliases_to_baseline": pa.uint8(), "relift_aliases_to_candidate": pa.uint8(),
    "relift_selected_kind": pa.uint8(), "relift_pairwise_baseline_equal": pa.uint8(),
    "relift_cache_skips": pa.uint8(),
    "relift_all_color_new": pa.uint8(),
    "perturbation_unique_stage1": pa.uint8(),
    "perturbation_unique_corrections": pa.uint8(),
    "perturbation_duplicate_member_fraction": pa.float64(),
    "perturbation_selected_member": pa.uint8(),
}


def _write_metric(directory: Path, name: str, values: np.ndarray) -> None:
    """Use the canonical two-column sidecar shape and atomic promotion."""
    dtype = _TYPES[name]
    schema = (_schema((name,)) if name in ("color_correlated_run", "relift_run")
              else pa.schema([pa.field("shot_index", pa.int64(), nullable=False),
                              pa.field(name, dtype, nullable=False)]))
    table = pa.table({"shot_index": pa.array(np.arange(len(values), dtype=np.int64)),
                      name: pa.array(values, type=dtype)}, schema=schema)
    if name in ("color_correlated_run", "relift_run"):
        _check_table(table, schema, 0)
    target = directory / f"{name}.parquet"
    temporary = directory / f".{name}.parquet.tmp"
    pq.write_table(table, temporary)
    os.replace(temporary, target)


def _write_weights(directory: Path, strategy: str, extra: dict, shots: int) -> None:
    weights = np.asarray(extra["candidate_weights"], dtype=np.float64)
    selected = np.asarray(extra["weights"], dtype=np.float64)
    basis = extra["candidate_weight_basis"]
    if weights.ndim != 3 or weights.shape[2] != shots or selected.shape != (shots,):
        raise ValueError(f"invalid {strategy} candidate weight shape")
    if not np.allclose(np.min(weights, axis=(0, 1)), selected):
        raise ValueError(f"{strategy} selected weights disagree with candidate tensor")
    flattened = np.moveaxis(weights, 2, 0).reshape(shots, -1)
    vector_type = pa.list_(pa.float64(), flattened.shape[1])
    metadata = {b"candidate_weight_basis": basis.encode(),
                b"candidate_shape": json.dumps(list(weights.shape[:2])).encode()}
    schema = pa.schema([pa.field("shot_index", pa.int64(), nullable=False),
                        pa.field("candidate_weights", vector_type, nullable=False),
                        pa.field("weights", pa.float64(), nullable=False)], metadata=metadata)
    table = pa.Table.from_arrays([pa.array(np.arange(shots), type=pa.int64()),
        pa.array(flattened.tolist(), type=vector_type), pa.array(selected)], schema=schema)
    target = directory / f"{strategy}_candidate_weights.parquet"
    temporary = directory / f".{strategy}_candidate_weights.parquet.tmp"
    pq.write_table(table, temporary)
    os.replace(temporary, target)


def read_weights(path: Path) -> tuple[np.ndarray, str, np.ndarray]:
    table = pq.read_table(path)
    indices = table.column("shot_index").to_numpy()
    if not np.array_equal(indices, np.arange(len(table))):
        raise ValueError("candidate weight shot indices differ")
    shape = json.loads(table.schema.metadata[b"candidate_shape"])
    basis = table.schema.metadata[b"candidate_weight_basis"].decode()
    values = np.asarray(table.column("candidate_weights").to_pylist(), dtype=float)
    weights = values.reshape((len(table), *shape)).transpose(1, 2, 0)
    selected = table.column("weights").to_numpy()
    if not np.allclose(np.min(weights, axis=(0, 1)), selected):
        raise ValueError("saved selected weights disagree with candidate weights")
    return weights, basis, selected


def audit_weights(code: ColorCode, extra: dict, shots: int) -> None:
    """Independently check unchanged-prior scoring on a bounded shot subset."""
    weights = np.asarray(extra["candidate_weights"])
    basis = extra["candidate_weight_basis"]
    native = extra["candidate_native_stage2_preds"]
    colors = extra["candidate_target_colors"]
    limit = min(shots, 4)
    for logical_class in range(weights.shape[0]):
        for slot, color in enumerate(colors):
            predictions = native[logical_class][slot]
            if predictions is None:
                continue
            base = code.dems_decomposed[color]
            if basis == "stage2":
                q = np.asarray(base.probs[1])
                expected = np.asarray(predictions[:limit], dtype=float) @ np.log((1 - q) / q)
            elif basis == "original_dem":
                mapped = base.map_errors_to_org_dem(np.asarray(predictions[:limit], dtype=bool), stage=2)
                q = np.asarray(code.probs_xz)
                expected = np.asarray(mapped, dtype=float) @ np.log((1 - q) / q)
            else:
                raise ValueError(f"unknown weight basis: {basis}")
            actual = weights[logical_class, slot, :limit]
            finite = np.isfinite(actual)
            if not np.allclose(expected[finite], actual[finite], rtol=1e-10, atol=1e-10):
                raise ValueError(f"candidate score audit failed: {color}, slot {slot}")


def run_paired(*, output_root: str | Path, shots: int = 16, distance: int = 3,
               physical_error_rate: float = .01, noise_model: str = "uniform",
               seed: int = 20260927, ensemble_size: int = 3, alpha: float = .2,
               weight_basis: str = "original_dem", batch_shots: int = 256) -> Path:
    if shots < 1 or distance < 3 or distance % 2 != 1 or ensemble_size < 1 or batch_shots < 1:
        raise ValueError("shots, odd distance and ensemble size must be positive")
    if weight_basis != "original_dem":
        raise ValueError("color-correlated paired benchmark requires original_dem selection basis")
    common = dict(d=distance, rounds=distance, circuit_type="tri",
                  cnot_schedule="tri_optimal", temp_bdry_type="Z",
                  noise_model=make_noise_model(noise_model, physical_error_rate),
                  remove_non_edge_like_errors=False,
                  color_correlated_weight_basis=weight_basis)
    codes = {
        "baseline": ColorCode(**common),
        "color_correlated": ColorCode(**(common | {"enable_colorcorrelated_decoding": True})),
        "relift": ColorCode(**(common | {"enable_cross_color_relifting": True})),
        "perturbation": ColorCode(**(common | {"enable_prior_perturbation": True,
            "perturbation_ensemble_size": ensemble_size, "perturbation_alpha": alpha,
            "perturbation_seed": seed})),
    }
    if any(code.circuit != codes["baseline"].circuit for code in codes.values()):
        raise ValueError("paired strategies have different physical circuits")
    metric_chunks = {name: [] for name in _TYPES}
    weight_chunks = {name: [] for name in ("color_correlated", "relift", "perturbation")}
    selected_weight_chunks = {name: [] for name in weight_chunks}
    bases = {}
    decode_seconds = {name: 0.0 for name in codes}
    batch_seeds = []
    for batch_id, shot_start in enumerate(range(0, shots, batch_shots)):
        batch_count = min(batch_shots, shots - shot_start)
        batch_seed = int(np.random.SeedSequence([seed, batch_id]).generate_state(1)[0])
        batch_seeds.append(batch_seed)
        detectors, actual = codes["baseline"].sample(batch_count, seed=batch_seed)
        predictions = {}
        extras = {}
        batch_seconds = {}
        for name, code in codes.items():
            started = perf_counter()
            predictions[name], extras[name] = code.decode(detectors, full_output=True)
            batch_seconds[name] = perf_counter() - started
            if name != "baseline":
                audit_weights(code, extras[name], batch_count)
        relift = extras["relift"]
        selected = np.asarray(relift["best_candidate_indices"], dtype=int)
        aliases = np.asarray(relift["candidate_alias_of"])
        if aliases.ndim != 3 or aliases.shape[1:] != (12, batch_count):
            raise ValueError("relift alias tensor has unexpected shape")
        # The selected logical class is found from the decoder's own selected score.
        weights = np.asarray(relift["candidate_weights"])
        selected_class = np.argmin(np.min(weights, axis=1), axis=0)
        chosen_aliases = aliases[selected_class, :, np.arange(batch_count)]
        if chosen_aliases.shape != (batch_count, 12):
            raise ValueError("relift alias indexing failed")
        extra_calls = np.asarray(relift["relift_extra_stage2_calls"], dtype=np.uint8)
        perturb = extras["perturbation"]
        stage1 = perturb["candidate_stage1_hypotheses"][0]
        corrections = perturb["candidate_original_corrections"][0]
        unique_stage1 = np.zeros(batch_count, dtype=np.uint8)
        unique_corrections = np.zeros(batch_count, dtype=np.uint8)
        duplicate_members = np.zeros(batch_count, dtype=float)
        for shot in range(batch_count):
            # Compare stage-1 hypotheses within each target graph; their column
            # order is color-specific. Final corrections share original ordering.
            unique_stage1[shot] = sum(len({stage1[3 * member + color][shot].tobytes()
                for member in range(ensemble_size)}) for color in range(3))
            unique_corrections[shot] = len({corrections[slot, shot].tobytes()
                for slot in range(3 * ensemble_size)})
            member_signatures = {tuple(corrections[3 * member + color, shot].tobytes()
                for color in range(3)) for member in range(ensemble_size)}
            duplicate_members[shot] = 1 - len(member_signatures) / ensemble_size
        correlated_executed = np.asarray(extras["color_correlated"]["candidate_executed"])[0]
        correlated_extra = 2 * np.count_nonzero(correlated_executed[3:], axis=0)
        relift_executed = np.asarray(relift["candidate_executed"])[0]
        metrics = {
            f"{name}_error": logical_errors(predictions[name], actual, batch_count)
            for name in codes
        }
        metrics.update(
            color_correlated_run=np.asarray(extras["color_correlated"]["color_correlated_run"], dtype=np.uint8),
            color_correlated_extra_mwpm_calls=np.asarray(
                correlated_extra, dtype=np.uint8),
            color_correlated_selected_kind=np.asarray(
                np.asarray(extras["color_correlated"]["best_candidate_indices"]) >= 3, dtype=np.uint8),
            relift_run=np.asarray(relift["relift_run_class"], dtype=np.uint8),
            relift_extra_stage2_calls=extra_calls,
            relift_total_mwpm_calls=np.asarray(6 + extra_calls, dtype=np.uint8),
            relift_candidate_slots=np.full(batch_count, 12, dtype=np.uint8),
            relift_unique_stage2_syndromes=np.asarray(3 + extra_calls, dtype=np.uint8),
            relift_aliases_to_baseline=np.count_nonzero((chosen_aliases >= 0) & (chosen_aliases < 3), axis=1).astype(np.uint8),
            relift_aliases_to_candidate=np.count_nonzero(chosen_aliases >= 3, axis=1).astype(np.uint8),
            relift_selected_kind=np.asarray([KINDS.index(relift["candidate_kinds"][slot]) for slot in selected], dtype=np.uint8),
            relift_pairwise_baseline_equal=np.asarray(relift["relift_pairwise_baseline_syndrome_equal"], dtype=np.uint8),
            relift_cache_skips=np.asarray(relift["relift_cache_skips"], dtype=np.uint8),
            relift_all_color_new=np.count_nonzero(relift_executed[9:12], axis=0).astype(np.uint8),
            perturbation_unique_stage1=unique_stage1,
            perturbation_unique_corrections=unique_corrections,
            perturbation_duplicate_member_fraction=duplicate_members,
            perturbation_selected_member=(np.asarray(perturb["best_candidate_indices"]) // 3).astype(np.uint8),
        )
        if not np.array_equal(metrics["color_correlated_run"], metrics["relift_run"]):
            raise ValueError("adaptive run classes disagree on the shared baseline corrections")
        if set(metrics) != set(_TYPES):
            raise ValueError("paired metric set differs from schema")
        for name, values in metrics.items():
            metric_chunks[name].append(values)
        for name in ("color_correlated", "relift", "perturbation"):
            weight_chunks[name].append(np.asarray(extras[name]["candidate_weights"]))
            selected_weight_chunks[name].append(np.asarray(extras[name]["weights"]))
            bases[name] = extras[name]["candidate_weight_basis"]
        for name, elapsed in batch_seconds.items():
            decode_seconds[name] += elapsed
    metrics = {name: np.concatenate(parts) for name, parts in metric_chunks.items()}
    extras = {name: {"candidate_weights": np.concatenate(weight_chunks[name], axis=2),
                     "weights": np.concatenate(selected_weight_chunks[name]),
                     "candidate_weight_basis": bases[name]}
              for name in weight_chunks}
    root = (Path(output_root).expanduser().resolve() / "adaptive_v2" /
            (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]))
    root.mkdir(parents=True, exist_ok=False)
    try:
        for name, values in metrics.items():
            _write_metric(root, name, values)
        for name in ("color_correlated", "relift", "perturbation"):
            _write_weights(root, name, extras[name], shots)
        manifest = {"schema_version": "adaptive_v2", "shots": shots,
            "distance": distance, "rounds": distance, "physical_error_rate": physical_error_rate,
            "noise_model": noise_model, "seed": seed, "ensemble_size": ensemble_size,
            "alpha": alpha, "candidate_weight_basis": weight_basis,
            "decode_seconds": decode_seconds,
            "nominal_max_mwpm_calls": {"baseline": 6, "color_correlated": 24,
                "relift": 15, "perturbation": 6 * ensemble_size},
            "selected_kind_codes": dict(enumerate(KINDS)), "batch_shots": batch_shots,
            "batch_seeds": batch_seeds, "batch_count": len(batch_seeds),
            "decoder_source": str(Path(__file__).resolve().parents[3] / "external_libs/color-code-stim")}
        identity = {key: manifest[key] for key in ("schema_version", "shots", "distance",
            "rounds", "physical_error_rate", "noise_model", "seed", "ensemble_size",
            "alpha", "candidate_weight_basis", "batch_shots")}
        manifest["configuration_id"] = sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        manifest["decoder_source_sha256"] = sha256(
            (Path(manifest["decoder_source"]) / "src/color_code_stim/decoders/concat_matching_decoder.py").read_bytes()
        ).hexdigest()
        temporary = root / ".manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        os.replace(temporary, root / "manifest.json")
    except Exception:
        (root / "FAILED").write_text("incomplete paired benchmark; do not analyze\n")
        raise
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default="results")
    parser.add_argument("--shots", type=int, default=16)
    parser.add_argument("--batch-shots", type=int, default=256)
    parser.add_argument("--distance", type=int, default=3)
    parser.add_argument("--physical-error-rate", type=float, default=.01)
    parser.add_argument("--noise-model", default="uniform")
    parser.add_argument("--seed", type=int, default=20260927)
    parser.add_argument("--ensemble-size", type=int, default=3)
    parser.add_argument("--alpha", type=float, default=.2)
    parser.add_argument("--weight-basis", choices=("original_dem",), default="original_dem")
    parser.add_argument("--ablation", action="store_true",
                        help="Run the full requested distance/p/basis/M/alpha grid")
    args = parser.parse_args()
    if args.ablation:
        for path in run_ablation(output_root=args.output_root, shots=args.shots, seed=args.seed):
            print(path)
        return
    print(run_paired(output_root=args.output_root, shots=args.shots,
        distance=args.distance, physical_error_rate=args.physical_error_rate,
        noise_model=args.noise_model, seed=args.seed,
        ensemble_size=args.ensemble_size, alpha=args.alpha, weight_basis=args.weight_basis,
        batch_shots=args.batch_shots))


def run_ablation(*, output_root: str | Path, shots: int, distances=(3, 5),
                 physical_error_rates=(.005, .01), bases=("original_dem",),
                 ensemble_sizes=(2, 4, 8, 16), alphas=(.25, .5, 1.),
                 seed: int = 20260927) -> list[Path]:
    """Run the requested grid; every strategy in a point shares physical shots.

    The baseline/adaptive rows repeat across perturbation settings deliberately:
    each saved point is independently paired and auditable.
    """
    paths = []
    for distance in distances:
        for p in physical_error_rates:
            for basis in bases:
                for size in ensemble_sizes:
                    for alpha in alphas:
                        paths.append(run_paired(output_root=output_root, shots=shots,
                            distance=distance, physical_error_rate=p, weight_basis=basis,
                            ensemble_size=size, alpha=alpha, seed=seed))
    return paths


if __name__ == "__main__":
    main()
