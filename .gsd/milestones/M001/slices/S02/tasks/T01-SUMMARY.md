---
id: T01
parent: S02
milestone: M001
provides:
  - Deterministic split/leakage validator core with unified gate payload schema (`pass`, `blocking_rule`, `reason`, `evidence`)
  - Unit-locked fail/pass contracts for R002 and R004 (including unknown split label + forbidden leakage column)
key_files:
  - mania_pipeline/scripts/split_leakage_contracts.py
  - mania_pipeline/tests/test_split_leakage_contracts.py
  - mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py
  - .gsd/milestones/M001/slices/S02/S02-PLAN.md
key_decisions:
  - D011: leakage checks use exact forbidden column set + explicit namespace allowlist (no keyword heuristics)
patterns_established:
  - Shared gate-result builder for both validators to keep error payload shape deterministic
  - Split authority sourced from `02_feature_engineering.py::assign_split` via dynamic import/cache
observability_surfaces:
  - Validator payloads expose blocking rule ID and structured evidence (`mismatches`, `unknown_labels`, `forbidden_columns`)
duration: ~1h
verification_result: passed
completed_at: 2026-03-14T16:52:00+03:00
blocker_discovered: false
---

# T01: Implement split/leakage validator contracts + unit tests

**Added standalone split/leakage contract validators with deterministic machine-readable gate payloads, and locked their pass/fail behavior with unit tests.**

## What Happened

- Implemented `mania_pipeline/scripts/split_leakage_contracts.py`:
  - `validate_split_contract(df, assign_split_fn=None)`
  - `validate_leakage_contract(df)`
  - shared `_build_gate_result(...)` helper producing canonical payload schema.
- Split contract behavior:
  - Fails on missing `Season`/`Split`.
  - Fails unknown split labels outside `Train/Val/Test`.
  - Uses `02_feature_engineering.py` `assign_split` as authority mapping and fails deterministic season-label mismatches.
  - Does **not** enforce season contiguity (avoids known false-fail risk).
- Leakage contract behavior:
  - Fails on missing canonical required columns (`Season`, `TeamA`, `TeamB`, `Target`, `Split`).
  - Fails exact forbidden raw/post-game leakage columns.
  - Enforces feature namespace contract (`*_diff` or explicit allowlist flags), without keyword scanning.
- Added `mania_pipeline/tests/test_split_leakage_contracts.py` covering:
  - valid dataframe pass path,
  - split season mismatch fail,
  - unknown split label fail,
  - forbidden leakage column fail,
  - payload shape assertions for both pass and fail paths.
- Added `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` scaffold contract tests for T02 integration wiring (currently expected to fail until stage wiring is done).
- Pre-flight fix applied: updated S02 verification list to include explicit failure-path diagnostic assertion command (`-k "fail"`).

## Verification

- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py`
  - 4 passed.
- ⚠️ Slice-level checks run (intermediate task; partial pass expected):
  - ❌ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_cli.py`
    - `test_run_pipeline_split_leakage_gate.py` fails because `run_pipeline.stage_feature` is not wired to gate execution/persistence yet (T02 scope).
  - ❌ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py -k "fail" -vv`
    - no fail-fast RuntimeError yet from `stage_feature` (T02 scope).
  - ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke`
    - canonical run succeeded.
  - ❌ `./venv/Scripts/python -c "... md['stage_outputs']['feature']['gates'] ..."`
    - `KeyError: 'gates'` since gate metadata is not wired yet (T02 scope).

## Diagnostics

- Validator fail payloads now expose inspectable evidence for future triage:
  - split mismatch: `evidence.mismatches`, `evidence.mismatch_count`
  - unknown label: `evidence.unknown_labels`
  - leakage forbidden columns: `evidence.forbidden_columns`
- Future agents can inspect unit contract behavior via:
  - `mania_pipeline/tests/test_split_leakage_contracts.py`
  - `mania_pipeline/scripts/split_leakage_contracts.py`

## Deviations

- Added `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` in T01 (ahead of T02) to satisfy first-task slice verification file creation requirement and lock integration expectations early.

## Known Issues

- Gate logic is not yet wired into `run_pipeline.py::stage_feature`; integration and metadata persistence checks remain failing until T02.

## Files Created/Modified

- `mania_pipeline/scripts/split_leakage_contracts.py` — new deterministic split/leakage validator contracts and shared gate payload helper.
- `mania_pipeline/tests/test_split_leakage_contracts.py` — unit tests for pass/fail and gate payload schema.
- `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` — integration contract test scaffold for T02 wiring.
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — added explicit failure-path diagnostic verification command; marked T01 complete.
- `.gsd/DECISIONS.md` — appended D011 gate-contract decision.
