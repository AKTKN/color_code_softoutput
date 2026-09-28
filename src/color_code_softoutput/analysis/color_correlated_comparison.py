"""Compose selected saved-run points without copying or pooling shot data."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from .color_correlated import ColorCorrelatedRun, PARAMETERS
from ..simulation import config as workflow_config


# These options change the physical circuit/observable being compared, unlike
# matching parameters, decomposition filtering, or the Monte Carlo shot count.
_PHYSICAL_DEFAULTS = {
    "temp_bdry_type": "Z", "superdense_circuit": False,
    "perfect_logical_initialization": False, "perfect_logical_measurement": False,
    "perfect_first_syndrome_extraction": False, "perfect_init_final": False,
}
_CONDITIONS = tuple(name for name in PARAMETERS
                    if name not in ("decoder_alias", "decoder_type"))


def _physical_options(point):
    options = dict(point.color_code_options) | dict(point.decoder_options)
    normalized = {name: options.get(name, default)
                  for name, default in _PHYSICAL_DEFAULTS.items()}
    boundary = normalized["temp_bdry_type"]
    if boundary is None:
        boundary = {"rec_stability": "r", "cult+growing": "Y"}.get(point.circuit_type, "Z")
    normalized["temp_bdry_type"] = boundary.upper()
    # ColorCode promotes perfect_init_final to both individual flags.
    if normalized["perfect_init_final"]:
        normalized["perfect_logical_initialization"] = True
        normalized["perfect_logical_measurement"] = True
    normalized.pop("perfect_init_final")
    return normalized


def _decoder_signature(point):
    options = dict(point.color_code_options) | dict(point.decoder_options)
    for key in _PHYSICAL_DEFAULTS:
        options.pop(key, None)
    decode = {key: value for key, value in point.decode_options
              if key not in ("compute_swim_distance", "full_output", "verbose", "check_validity")}
    return point.decoder_type, tuple(sorted(options.items())), tuple(sorted(decode.items()))


class ColorCorrelatedComparison(ColorCorrelatedRun):
    """Use the normal LER/table API across selected runs.

    ``primary_run`` supplies the export directory and preferred representative
    baselines. Each item in ``additional_sources`` is a mapping containing
    ``run_directory`` and optional ``filter`` and ``alias_map``. Aliases can be
    renamed for this view without editing saved configs or files. Duplicate
    alias/condition points are rejected, never pooled or silently replaced.
    Imported unpaired decoders use a matching baseline, preferring the primary
    run; paired decoders always retain their own saved baseline.
    """

    def __init__(self, primary_run: str | Path | ColorCorrelatedRun, *,
                 additional_sources: Sequence[Mapping] = ()):
        if isinstance(additional_sources, (str, bytes, Mapping)):
            raise ValueError("additional_sources must be a sequence of source mappings")
        primary = (primary_run if isinstance(primary_run, ColorCorrelatedRun)
                   else ColorCorrelatedRun(primary_run))
        if isinstance(primary, ColorCorrelatedComparison):
            raise ValueError("primary_run must be a single saved run")
        self.run_directory = primary.run_directory
        self.run_log = primary.run_log
        self.config = primary.config
        self._cache = {}
        self._owners = {}
        self._point_dirs = {}
        sources, frames, manifest = [], [], []
        seen_points, physical, methods = set(), {}, {}
        specifications = [{"run_directory": primary.run_directory}, *additional_sources]
        for priority, spec in enumerate(specifications):
            if (not isinstance(spec, Mapping) or "run_directory" not in spec
                    or set(spec) - {"run_directory", "filter", "alias_map"}):
                raise ValueError("Each source needs run_directory and optional filter/alias_map")
            source = primary if priority == 0 else ColorCorrelatedRun(spec["run_directory"])
            frame = source.select(spec.get("filter"))
            alias_map = spec.get("alias_map", {})
            if not isinstance(alias_map, Mapping):
                raise ValueError("alias_map must map selected decoder aliases to new aliases")
            if set(alias_map) - set(frame.decoder_alias):
                raise ValueError("alias_map contains aliases not selected by the source filter")
            for alias in alias_map.values():
                workflow_config._string(alias, "alias_map")
            original_names = frame.point_directory.to_list()
            frame["decoder_alias"] = frame.decoder_alias.map(lambda alias: alias_map.get(alias, alias))
            frame["source_priority"] = priority
            for row, name in zip(frame.itertuples(), original_names):
                point = source._point_dirs[name]
                condition = tuple(getattr(row, key) for key in _CONDITIONS)
                identity = (row.decoder_alias, condition)
                if identity in seen_points:
                    raise ValueError(f"Duplicate decoder_alias/physical condition: {identity}; "
                                     "filter the source or use alias_map")
                settings = _physical_options(point)
                physical_context = (row.circuit_type, row.noise_model, row.cnot_schedule)
                if physical_context in physical and settings != physical[physical_context]:
                    raise ValueError(f"Incompatible physical circuit options at {condition}")
                method = _decoder_signature(point)
                if row.decoder_alias in methods and method != methods[row.decoder_alias]:
                    raise ValueError(f"Different decoder settings share alias {row.decoder_alias}; "
                                     "use alias_map to distinguish them")
                seen_points.add(identity)
                physical[physical_context] = settings
                methods[row.decoder_alias] = method
                key = str(source.run_directory / name)
                if key in self._owners:
                    raise ValueError(f"Duplicate saved point: {key}; filter the source")
                self._owners[key] = (source, name)
                self._point_dirs[key] = point
            # Absolute composite identities avoid collisions across date folders;
            # data_directory/source_run still identify the untouched saved files.
            frame["point_directory"] = frame.data_directory
            frames.append(frame)
            sources.append(source)
            manifest.append({"run_directory": str(source.run_directory),
                             "filter": dict(spec.get("filter") or {}),
                             "alias_map": dict(alias_map), "selected_points": len(frame)})
        self.source_runs = tuple(sources)
        self.source_manifest = manifest
        self.catalog = pd.concat(frames, ignore_index=True)

    def _summarize_point(self, name):
        if name not in self._cache:
            owner, original_name = self._owners[name]
            record = owner._summarize_point(original_name).copy()
            record["point_directory"] = name
            self._cache[name] = record
        return self._cache[name]
