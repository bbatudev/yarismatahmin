---
id: T01
parent: S01
milestone: M001
provides:
  - Pytest baseline and contract-first test suite for canonical orchestrator run context + stage lifecycle behavior
key_files:
  - mania_pipeline/environment.yml
  - mania_pipeline/pytest.ini
  - mania_pipeline/tests/test_run_context_contract.py
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - .gsd/milestones/M001/slices/S01/tasks/T01-PLAN.md
  - .gsd/milestones/M001/slices/S01/S01-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/STATE.md
key_decisions:
  - Added D008: `run_pipeline.py` test seam contract (`build_run_context`, `main`, `CANONICAL_STAGES`, `STAGE_HANDLERS`) to keep lifecycle tests deterministic with monkeypatched stage stubs
patterns_established:
  - Contract-first gating: explicit sentinel failure when canonical orchestrator file is absent, then deeper schema/lifecycle assertions once file exists
observability_surfaces:
  - `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py -q` for machine-readable contract drift detection
  - Sentinel assertion message explicitly names missing `mania_pipeline/scripts/run_pipeline.py`
duration: 1h
verification_result: passed
completed_at: 2026-03-14T16:58:00+03:00
blocker_discovered: false
---

# T01: Establish orchestrator contract tests and pytest baseline

**Added pytest baseline + orchestrator contract tests so T02 implementation is forced to satisfy run-context and lifecycle schemas instead of ad-hoc logging behavior.**

## What Happened

- Pre-flight fix applied: added `## Observability Impact` section to `.gsd/milestones/M001/slices/S01/tasks/T01-PLAN.md` with concrete runtime/test signals and failure visibility.
- Updated `mania_pipeline/environment.yml` to include `pytest` dependency.
- Added `mania_pipeline/pytest.ini` with discovery defaults (`testpaths=tests`, `python_files=test_*.py`, `-ra`).
- Created `mania_pipeline/tests/test_run_context_contract.py`:
  - Asserts required run context fields (`run_id`, `seed`, `git_commit`, `started_at`, `command`, `cwd`)
  - Asserts type/format requirements (ISO-8601 timestamp, non-empty string fields, integer seed)
  - Includes negative-path check that removing any required field fails contract assertion.
- Created `mania_pipeline/tests/test_run_pipeline_cli.py`:
  - Asserts lifecycle event schema fields (`stage`, `status`, `started_at`, `finished_at`, `duration_ms`, `error`)
  - Uses monkeypatched stage stubs through `STAGE_HANDLERS` to validate success and failure event flows (`started/succeeded/failed`) and stop-on-failure behavior.
  - Verifies CLI seed propagation into `run_metadata.json` in success path.
- Reduced red-signal noise by using one explicit per-file sentinel failure (`run_pipeline.py` missing) and skipping deeper tests until orchestrator file exists.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py -q`
  - Initial run failed with `No module named pytest`.
  - Installed baseline runner: `./venv/Scripts/python -m pip install pytest`.
  - Re-run result: **2 failed, 9 skipped**.
    - Failures are intentional sentinels: missing `mania_pipeline/scripts/run_pipeline.py`.
    - This leaves a clear red gate for T02 while preserving contract assertions for green path.
- Slice verification command (runtime):
  - `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke` → failed (`run_pipeline.py` not found)
  - Metadata/event contract check command → failed (`no run dir`)

## Diagnostics

- Contract inspection surfaces:
  - `mania_pipeline/tests/test_run_context_contract.py`
  - `mania_pipeline/tests/test_run_pipeline_cli.py`
- Current failure signature expected before T02:
  - `Missing canonical orchestrator script: .../mania_pipeline/scripts/run_pipeline.py. Implement it in T02.`
- After T02 creates the script, skipped tests auto-activate and enforce full schema/lifecycle assertions.

## Deviations

- None.

## Known Issues

- `mania_pipeline/scripts/run_pipeline.py` does not exist yet; slice-level runtime verification remains red until T02 implementation.

## Files Created/Modified

- `mania_pipeline/environment.yml` — added `pytest` dependency.
- `mania_pipeline/pytest.ini` — added pytest discovery/runtime defaults.
- `mania_pipeline/tests/test_run_context_contract.py` — run context schema + seed propagation + negative-path contract tests.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — CLI lifecycle event contract tests with monkeypatched stage stubs.
- `.gsd/milestones/M001/slices/S01/tasks/T01-PLAN.md` — added missing `## Observability Impact` pre-flight section.
- `.gsd/milestones/M001/slices/S01/S01-PLAN.md` — marked T01 as completed (`[x]`).
- `.gsd/DECISIONS.md` — appended D008 for orchestrator test seam contract.
- `.gsd/STATE.md` — advanced Next Action to T02 and recorded the latest decision.
