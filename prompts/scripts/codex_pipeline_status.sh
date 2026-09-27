#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="$ROOT/.codex-pipeline/near-optimal"
SESSION="${CODEX_TMUX_SESSION:-codex-near-optimal}"

echo "Repository: $ROOT"
echo "Branch:     $(git -C "$ROOT" branch --show-current)"
echo "HEAD:       $(git -C "$ROOT" log -1 --oneline)"
echo "Decoder:    $(git -C "$ROOT/external_libs/color-code-stim" branch --show-current)"
echo

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux:       session '$SESSION' exists"
else
  echo "tmux:       session '$SESSION' does not exist"
fi

if [[ -f "$STATE_DIR/exit-code" ]]; then
  echo "Exit code:  $(cat "$STATE_DIR/exit-code")"
fi

echo
echo "Recent root commits:"
git -C "$ROOT" --no-pager log --oneline -5
echo
echo "Recent decoder commits:"
git -C "$ROOT/external_libs/color-code-stim" --no-pager log --oneline -5

echo
echo "Latest structured results:"
if [[ -d "$STATE_DIR/results" ]]; then
  ls -1t "$STATE_DIR/results"/*.json 2>/dev/null | head -5 || true
else
  echo "(none)"
fi

echo
echo "Root working tree:"
git -C "$ROOT" status --short
echo
echo "Decoder working tree:"
git -C "$ROOT/external_libs/color-code-stim" status --short
