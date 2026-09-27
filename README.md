# color-code-softoutput

Research code for paired color-code soft-output experiments and analysis. The
Python package is in `src/color_code_softoutput/`; reproducible workflows are in
`notebooks/`, with tests in `tests/`. The mathematical notes and implementation
records are in `notes/`, `STATUS.md`, and `REVIEW.md`.

## Setup

This project uses modified decoder forks with APIs that are absent from the
standard PyMatching and color-code-stim releases. Clone them into the ignored
`external_libs/` directory before running the code-capacity and circuit-level
SWIM workflows:

```bash
git clone https://github.com/AKTKN/color_code_softoutput.git
cd color_code_softoutput
mkdir -p external_libs
git clone --branch phase2a/swim-distance https://github.com/AKTKN/PyMatching.git external_libs/PyMatching
git clone --branch phase2a/swim-distance https://github.com/AKTKN/color-code-stim.git external_libs/color-code-stim
conda env create -f environment.yml
conda run -n color_code_so env DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=4 python -m pip install --no-build-isolation -e external_libs/PyMatching -e external_libs/color-code-stim -e '.[test,notebook]'
conda run -n color_code_so python -m pytest tests -q
```

The path-gap, monotone-Y, and surface-code path-gap experiments use separate
feature checkouts and, in some cases, local work in progress. Their source
paths and validation state are recorded in `STATUS.md` and the corresponding
`notes/support/` reports. The command above sets up the main SWIM workflow;
it does not install those optional feature variants.

Start with `notebooks/phase2a_getting_started.ipynb` for code-capacity
experiments or `notebooks/circuit_level_getting_started.ipynb` for closed-memory
circuit experiments. The package-level usage guide is
[`src/color_code_softoutput/README.md`](src/color_code_softoutput/README.md).

## Repository contents

This repository tracks source code, tests, notebook documents, prompts, and
research notes. Local decoder checkouts, build outputs, caches, saved results,
and third-party reference PDFs are excluded by `.gitignore`. Generated notebook
outputs already embedded in the notebook documents are retained. The TeX source
for project notes is included; generated PDFs are not. GitHub publication is a
source release, not a PyPI upload or a claim of calibrated confidence scores.
