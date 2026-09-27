#!/usr/bin/env bash
set -euo pipefail

# Launch the Codex pipeline inside a detached tmux session.
# The tmux session remains open after pipeline completion/failure so the final
# terminal state can be inspected. Exit the shell in tmux or kill the session
# when finished.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
RUNNER="$ROOT/prompts/scripts/run_codex_pipeline.sh"
STATE_DIR="$ROOT/.codex-pipeline/near-optimal"
LOG_FILE="$STATE_DIR/pipeline.log"
EXIT_FILE="$STATE_DIR/exit-code"
SESSION="${CODEX_TMUX_SESSION:-codex-near-optimal}"

command -v tmux >/dev/null 2>&1 || {
  echo "ERROR: tmux is not installed." >&2
  exit 1
}

[[ -x "$RUNNER" ]] || {
  echo "ERROR: runner is missing or not executable: $RUNNER" >&2
  exit 1
}

mkdir -p "$STATE_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  cat >&2 <<EOF
ERROR: tmux session '$SESSION' already exists.

Attach:
  tmux attach -t $SESSION

Or remove it:
  tmux kill-session -t $SESSION
EOF
  exit 1
fi

rm -f -- "$EXIT_FILE"

# Quote all arguments safely for the shell that will run inside tmux.
printf -v RUNNER_Q '%q' "$RUNNER"
printf -v ROOT_Q '%q' "$ROOT"
printf -v LOG_Q '%q' "$LOG_FILE"
printf -v EXIT_Q '%q' "$EXIT_FILE"
printf -v SANDBOX_Q '%q' "${CODEX_PIPELINE_SANDBOX:-workspace-write}"
ARGS_Q=""
for arg in "$@"; do
  printf -v q '%q' "$arg"
  ARGS_Q+=" $q"
done

INNER="cd $ROOT_Q; set -o pipefail; CODEX_PIPELINE_SANDBOX=$SANDBOX_Q $RUNNER_Q$ARGS_Q 2>&1 | tee -a $LOG_Q; rc=\${PIPESTATUS[0]}; printf '%s\n' "\$rc" > $EXIT_Q; echo; echo \"Pipeline exit code: \$rc\"; echo \"Press Ctrl-D or run 'exit' to close this tmux session.\"; exec bash"

tmux new-session -d -s "$SESSION" "bash -lc $(printf '%q' "$INNER")"

cat <<EOF
Started near-optimal Codex pipeline in detached tmux session:

  session: $SESSION
  log:     $LOG_FILE
  exit:    $EXIT_FILE

Attach interactively:
  tmux attach -t $SESSION

Detach again:
  Ctrl-b d

Watch the log without attaching:
  tail -f "$LOG_FILE"

Check whether the session exists:
  tmux has-session -t "$SESSION" && echo running

When finished, close it from inside with 'exit', or:
  tmux kill-session -t "$SESSION"
EOF
