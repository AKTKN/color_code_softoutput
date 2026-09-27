#!/usr/bin/env bash
#PBS -N color_code_so
#PBS -j oe
#PBS -l select=1:ncpus=2:mem=8gb
#PBS -l walltime=01:00:00

set -euo pipefail

cd "${PBS_O_WORKDIR:?Submit this script with qsub from the repository root}"

if [[ -n "${CONDA_BASE:-}" ]]; then
    conda_base="$CONDA_BASE"
elif command -v conda >/dev/null 2>&1; then
    conda_base="$(conda info --base)"
else
    printf '%s\n' 'Anaconda is unavailable. Load the site Anaconda module or pass CONDA_BASE with qsub -v.' >&2
    exit 1
fi

source "$conda_base/etc/profile.d/conda.sh"
conda activate color_code_so

# Each simulation worker is a process; keep BLAS libraries single threaded.
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

config_file="${CONFIG_FILE:-configs/example.yaml}"
python -m color_code_softoutput.simulation.cli --config "$config_file"
