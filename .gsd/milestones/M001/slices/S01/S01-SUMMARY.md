---
id: S01
parent: M001
milestone: M001
provides:
  - Canonical `run_pipeline` CLI with deterministic stage order (`feature -> train -> eval_report -> artifact`) and run-scoped metadata/lifecycle artifacts
requires: []
affects:
  - S02
  - S03
  - S06
  - S07
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/scripts/03_lgbm_train.py
  - mania_pipeline/tests/test_run_context_contract.py
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - mania_pipeline/artifacts/runs/<run_id>/run_metadata.json
  - mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/PROJECT.md
  - .gsd/STATE.md
key_decisions:
  - D008: `run_pipeline.py` must expose a stable test seam (`build_run_context`, `main`, `CANONICAL_STAGES`, `STAGE_HANDLERS`) for deterministic lifecycle contract tests
  - D009: Numeric-prefixed scripts are dynamically loaded with absolute path rebinding to keep canonical orchestration deterministic across caller cwd
patterns_established:
  - Contract-first orchestration gating with explicit schema assertions for run context and stage lifecycle JSONL events
  - Stage lifecycle wrapper that always writes `started` then `succeeded`/`failed` and hard-stops the run on first failed stage
observability_surfaces:
  - `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`
  - `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl`
  - `mania_pipeline/artifacts/runs/<run_id>/eval_report.json`
  - `mania_pipeline/artifacts/runs/<run_id>/artifact_manifest.json`
  - `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py`
drill_down_paths:
  - .gsd/milestones/M001/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S01/tasks/T02-SUMMARY.md
duration: 2h30m
verification_result: passed
completed_at: 2026-03-14T17:35:00+03:00
---

# S01: Canonical Run Orchestrator

**Shipped a single canonical command that runs real feature/train/eval/artifact stages end-to-end with machine-readable run metadata and failure-aware lifecycle events.**

## What Happened

T01 established the pytest baseline and locked the contract shape before implementation: required run-context keys, lifecycle event schema, and deterministic success/fail behavior through monkeypatched stage handlers.

T02 implemented `mania_pipeline/scripts/run_pipeline.py` with deterministic stage order, real Python-level wiring to feature and training scripts, per-run artifact directory creation, and JSON/JSONL outputs (`run_metadata.json`, `stage_events.jsonl`, `eval_report.json`, `artifact_manifest.json`). Failure handling now records structured error payloads and returns non-zero exit immediately.

During smoke verification, a Windows console encoding break in training output was detected and fixed (ASCII divider), then the canonical run passed on real data.

## Verification

Executed all slice-level checks from `S01-PLAN`:

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py` → **11 passed**
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke` → **passed** (latest run: `mania_pipeline/artifacts/runs/20260314T143023Z_s01_smoke`)
- `./venv/Scripts/python -c "...S01 contract verified..."` (metadata keys + succeeded stage order assertion) → **passed**

Observability surface confirmation:

- Verified required run artifacts exist in latest run directory:
  - `run_metadata.json`
  - `stage_events.jsonl`
  - `eval_report.json`
  - `artifact_manifest.json`

## Requirements Advanced

- R010 — S01 stabilized run metadata/lifecycle artifact surfaces consumed by later artifact-contract enforcement.
- R018 — S01 created deterministic per-run structured outputs that later regression delta/gating logic will compare.

## Requirements Validated

- R001 — Canonical end-to-end run command is now proven by passing real-runtime execution and contract checks.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Split/leakage fail-fast gates are not yet implemented (S02).
- Notebook/script execution-path enforcement is not yet implemented (S03).
- Current Windows shell still renders some Turkish console text with mojibake; execution is unaffected.

## Follow-ups

- Implement S02 deterministic split validator + leakage checker using S01 stage lifecycle hooks.
- Add blocking gate result schema (`pass/fail`, `reason`, `blocking_rule`) and integrate into canonical run flow.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — Canonical orchestrator CLI and lifecycle logging.
- `mania_pipeline/scripts/03_lgbm_train.py` — Seeded training hook + ASCII-safe output fix.
- `mania_pipeline/tests/test_run_context_contract.py` — Run context contract tests.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — Lifecycle success/failure contract tests.
- `README.md` — Canonical command and artifact locations.
- `.gsd/REQUIREMENTS.md` — Moved R001 to Validated with S01 proof.
- `.gsd/milestones/M001/M001-ROADMAP.md` — Marked S01 complete.
- `.gsd/PROJECT.md` — Refreshed current-state narrative after S01 delivery.
- `.gsd/STATE.md` — Advanced state to slice-complete and next action.
- `.gsd/milestones/M001/slices/S01/S01-SUMMARY.md` — Slice-level compressed delivery summary.

## Forward Intelligence

### What the next slice should know
- `stage_events.jsonl` is already a reliable insertion point for S02 gate outcomes; piggybacking on this avoids a second logging surface.
- Stage wiring currently executes feature generation for both genders in one `feature` stage call; leakage/split diagnostics should still emit gender-specific detail inside gate payloads.

### What's fragile
- `03_lgbm_train.py` console output still depends on host code page for display quality — keep logs ASCII-safe where possible to avoid noisy false alarms.

### Authoritative diagnostics
- `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl` — single source of truth for stage order, timing, and failure payload.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — fastest drift detector for CLI lifecycle contract.

### What assumptions changed
- “Canonical orchestrator missing” — now false; orchestration exists and passes real-data smoke validation.
- “Run contract is only planned” — now false; metadata/event schema is implemented and enforced by tests.
