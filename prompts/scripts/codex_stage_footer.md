---

# Pipeline completion contract

This task is being executed by the adaptive near-optimal six-stage Codex pipeline.
The workspace root and decoder checkout are separate Git repositories.
Inspect both before editing, preserve pre-existing local changes, and use the
paths given in the pipeline context.

Your final response MUST satisfy the JSON schema supplied through
`codex exec --output-schema`.

Set:

- `"status": "success"` and `"next_stage_safe": true` only if the requested
  deliverables for this stage are complete and the required tests/checks for
  this stage pass.
- `"status": "blocked"` and `"next_stage_safe": false` if a repository/API/
  scientific assumption conflicts with the prompt and proceeding would require
  inventing a convention or making an unauthorized decision.
- `"status": "failed"` and `"next_stage_safe": false` if implementation remains
  broken, a required test fails, or a required deliverable is incomplete.

Additional rules:

1. Do not report success merely because partial implementation was completed.
2. If a test is intentionally not applicable, record it as `"not_run"` and
   explain why in `"notes"`.
3. `"changed_files"` should list repository-relative paths you changed in this
   stage.
4. `"blocking_issue"` must be `null` on success and a concise explanation on
   blocked/failed outcomes.
5. Do not commit, push, merge, rebase, or modify Git history. The outer pipeline may perform local checkpoint commits only when explicitly
   started with `--checkpoint`.
