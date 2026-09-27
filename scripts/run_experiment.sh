#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:?usage: $0 CONFIG.yaml}"
shift

python -m color_code_softoutput.simulation.cli --config "$CONFIG" "$@"
