#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
DECODER="$ROOT/external_libs/color-code-stim"
PROMPT_DIR="$ROOT/prompts"
SCHEMA="$SCRIPT_DIR/codex_stage_result_schema.json"
FOOTER="$SCRIPT_DIR/codex_stage_footer.md"
STATE_DIR="$ROOT/.codex-pipeline/near-optimal"
RESULT_DIR="$STATE_DIR/results"
STDOUT_DIR="$STATE_DIR/stdout"
STDERR_DIR="$STATE_DIR/stderr"

STAGES=(
  '01_shared_candidate_scoring.md'
  '02_cross_color_relifting.md'
  '03_xz_dem_perturbation_ensemble.md'
  '04_integration_regression.md'
  '05_softoutput_experiment_integration(1).md'
  '06_ablation_benchmark.md'
)

FROM_STAGE=''
CHECKPOINT=0
LIST_ONLY=0

usage() {
  cat <<'USAGE'
Usage: prompts/scripts/run_codex_pipeline.sh [--from STAGE] [--checkpoint] [--list]

Stages 01-04 run in external_libs/color-code-stim; stages 05-06 run in the
workspace root. The theory file and prompt are supplied to every stage.
By default, existing work is preserved and no Git commits are made.

  --from STAGE    Start at a stage number, stem, or exact filename (e.g. 03).
  --checkpoint    Require both repositories clean at start; after each
                  successful stage, commit changes in each affected repository.
  --list          Print stages and exit without running Codex.

Environment:
  CODEX_PIPELINE_SANDBOX  Codex sandbox mode (default: workspace-write).
  CODEX_PIPELINE_ADD_DIR  Optional additional writable directory.
USAGE
}

while (( $# )); do
  case "$1" in
    --from)
      (( $# >= 2 )) || { echo 'ERROR: --from needs a stage.' >&2; exit 2; }
      FROM_STAGE="$2"; shift 2 ;;
    --checkpoint) CHECKPOINT=1; shift ;;
    --list) LIST_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

start_index=0
if [[ -n "$FROM_STAGE" ]]; then
  found=0
  for i in "${!STAGES[@]}"; do
    stem="${STAGES[$i]%.md}"
    if [[ "$FROM_STAGE" == "${STAGES[$i]}" || "$FROM_STAGE" == "$stem" || "$FROM_STAGE" == "${stem%%_*}" ]]; then
      start_index="$i"; found=1; break
    fi
  done
  (( found )) || { echo "ERROR: unknown stage: $FROM_STAGE" >&2; exit 2; }
fi

if (( LIST_ONLY )); then
  for i in "${!STAGES[@]}"; do
    (( i < start_index )) && continue
    if (( i < 4 )); then location='decoder'; else location='root'; fi
    printf '%s  [%s]\n' "${STAGES[$i]}" "$location"
  done
  exit 0
fi

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing command: $1" >&2; exit 1; }
}
require_cmd codex
require_cmd jq
require_cmd git

[[ -d "$DECODER/.git" ]] || { echo "ERROR: independent decoder checkout missing: $DECODER" >&2; exit 1; }
[[ -f "$PROMPT_DIR/near_optimal_color_code_theory.tex" ]] || { echo 'ERROR: theory file missing.' >&2; exit 1; }
[[ -f "$SCHEMA" && -f "$FOOTER" ]] || { echo 'ERROR: result schema or stage footer missing.' >&2; exit 1; }
for prompt in "${STAGES[@]}"; do
  [[ -f "$PROMPT_DIR/$prompt" ]] || { echo "ERROR: prompt missing: $PROMPT_DIR/$prompt" >&2; exit 1; }
done

SANDBOX_MODE="${CODEX_PIPELINE_SANDBOX:-workspace-write}"
case "$SANDBOX_MODE" in
  workspace-write|read-only|danger-full-access) ;;
  *) echo "ERROR: invalid sandbox mode: $SANDBOX_MODE" >&2; exit 2 ;;
esac

for repo in "$ROOT" "$DECODER"; do
  [[ -n "$(git -C "$repo" branch --show-current)" ]] || { echo "ERROR: detached HEAD: $repo" >&2; exit 1; }
  if (( CHECKPOINT )); then
    [[ -z "$(git -C "$repo" status --porcelain)" ]] || { echo "ERROR: --checkpoint requires a clean repository: $repo" >&2; exit 1; }
    git -C "$repo" config user.name >/dev/null && git -C "$repo" config user.email >/dev/null || {
      echo "ERROR: Git commit identity is missing: $repo" >&2; exit 1;
    }
  fi
done

mkdir -p "$RESULT_DIR" "$STDOUT_DIR" "$STDERR_DIR"
echo "Root: $ROOT ($(git -C "$ROOT" branch --show-current))"
echo "Decoder: $DECODER ($(git -C "$DECODER" branch --show-current))"
echo "Start: ${STAGES[$start_index]}"
echo "Checkpoint commits: $CHECKPOINT"
echo "Sandbox: $SANDBOX_MODE"

for i in "${!STAGES[@]}"; do
  (( i < start_index )) && continue
  prompt_file="${STAGES[$i]}"
  stage="${prompt_file%.md}"
  result_path="$RESULT_DIR/$stage.json"
  stdout_path="$STDOUT_DIR/$stage.log"
  stderr_path="$STDERR_DIR/$stage.log"
  if (( i < 4 )); then
    workdir="$DECODER"
    otherdir="$ROOT"
  else
    workdir="$ROOT"
    otherdir="$DECODER"
  fi

  rm -f -- "$result_path" "$stdout_path" "$stderr_path"
  echo
  echo "Starting $stage in $workdir"
  extra_dirs=(--add-dir "$otherdir")
  if [[ -n "${CODEX_PIPELINE_ADD_DIR:-}" ]]; then
    extra_dirs+=(--add-dir "$CODEX_PIPELINE_ADD_DIR")
  fi

  set +e
  {
    printf 'Pipeline context: workspace root is %s; independent decoder repository is %s.\n' "$ROOT" "$DECODER"
    printf 'Work from %s. Read the complete theory file at %s before editing.\n' "$workdir" "$PROMPT_DIR/near_optimal_color_code_theory.tex"
    printf 'Inspect both Git working trees first. Preserve all existing local edits.\n'
    printf 'This is stage %s of 06. Complete its requested tests, then stop.\n\n' "${stage%%_*}"
    cat -- "$PROMPT_DIR/$prompt_file"
    printf '\n\n'
    cat -- "$FOOTER"
  } | codex exec \
      --sandbox "$SANDBOX_MODE" \
      --config approval_policy=never \
      --color never \
      -C "$workdir" \
      "${extra_dirs[@]}" \
      --output-schema "$SCHEMA" \
      -o "$result_path" \
      - \
      2> >(tee "$stderr_path" >&2) | tee "$stdout_path"
  codex_rc=${PIPESTATUS[1]}
  set -e

  if (( codex_rc != 0 )); then
    echo "ERROR: Codex exited $codex_rc at $stage. Changes are preserved." >&2
    exit "$codex_rc"
  fi
  [[ -s "$result_path" ]] && jq -e . "$result_path" >/dev/null || {
    echo "ERROR: missing or invalid result JSON: $result_path" >&2; exit 1;
  }
  jq . "$result_path"
  if [[ "$(jq -r '.status' "$result_path")" != success || "$(jq -r '.next_stage_safe' "$result_path")" != true ]] ||
     ! jq -e 'all(.tests[]; .result != "failed") and .blocking_issue == null' "$result_path" >/dev/null; then
    echo "PIPELINE STOPPED at $stage: $(jq -r '.blocking_issue // .summary' "$result_path")" >&2
    exit 1
  fi

  if (( CHECKPOINT )); then
    for repo in "$DECODER" "$ROOT"; do
      if [[ -n "$(git -C "$repo" status --porcelain)" ]]; then
        git -C "$repo" add -A
        git -C "$repo" commit -m "codex pipeline: $stage"
        echo "Checkpoint: $repo $(git -C "$repo" rev-parse --short HEAD)"
      fi
    done
  fi
  echo "SUCCESS: $stage"
done

echo 'All six near-optimal Codex stages completed successfully.'
