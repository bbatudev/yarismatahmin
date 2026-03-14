---
id: T02
parent: S02
milestone: M001
provides:
  - Feature-stage split/leakage gates are enforced before train with fail-fast `RuntimeError` carrying `blocking_rule`
  - Pass-path gate diagnostics are persisted under `run_metadata.json -> stage_outputs.feature.gates.{men,women}`
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - .gsd/milestones/M001/slices/S02/S02-PLAN.md
  - .gsd/DECISIONS.md
key_decisions:
  - D012: persist canonical aggregate gender gate payload with nested split/leakage evidence under feature stage outputs
patterns_established:
  - Gate wrapper composes validator payloads into one deterministic per-gender contract result and raises on first blocking rule
observability_surfaces:
  - mania_pipeline/artifacts/runs/<run_id>/run_metadata.json (`stage_outputs.feature.gates.{men,women}`)
  - mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl (`feature` failed event includes blocking rule in `error.message`)
  - mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py
duration: ~1h
verification_result: passed
completed_at: 2026-03-14T17:56:32+03:00
blocker_discovered: false
---

# T02: Wire gates into canonical feature stage + fail-fast integration tests

**Wired split/leakage validators into canonical `feature` stage with fail-fast blocking behavior and persisted per-gender gate diagnostics.**

## What Happened

- Updated `mania_pipeline/scripts/run_pipeline.py`:
  - Added lazy loader wrappers for `validate_split_contract` / `validate_leakage_contract` from `split_leakage_contracts.py`.
  - Added feature gate composition helpers to build deterministic aggregate payload per gender:
    - `pass`, `blocking_rule`, `reason`, `evidence`
    - nested `evidence.split` + `evidence.leakage` payloads.
  - `stage_feature` now runs split + leakage gates for both men/women immediately after dataframe generation.
  - On any failure, raises `RuntimeError` with `blocking_rule` in message (fail-fast at `feature` stage).
  - On pass, persists gate payloads in feature output as `stage_outputs.feature.gates`.
- Rewrote `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` to CLI-level integration tests:
  - fail scenario: non-zero exit, `feature` failed event only, `blocking_rule` present in failed event error message.
  - pass scenario: success exit, canonical stage order preserved, gate payload persisted under metadata for both genders.
- `mania_pipeline/tests/test_run_pipeline_cli.py` remained valid; no assertion changes required for stage-order contract.

## Verification

- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py`
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_cli.py`
- ✅ `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py -k "fail" -vv`
- ✅ `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke`
- ✅ `./venv/Scripts/python -c "import json, pathlib; run=max(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s02_split_leakage_smoke'), key=lambda p: p.stat().st_mtime_ns); md=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass']; print('S02 gate metadata contract ok')"`

## Diagnostics

- Pass-path inspection:
  - `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`
  - path: `stage_outputs.feature.gates.men` and `.women`
  - includes aggregate gate status and nested split/leakage evidence payload.
- Fail-path inspection:
  - `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl`
  - `feature` failed event `error.message` now includes `blocking_rule` for machine-usable triage.

## Deviations

- none

## Known Issues

- none

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — feature-stage gate wiring, fail-fast blocking rule error, and gate payload persistence.
- `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` — CLI-level fail-fast and pass-persist integration tests.
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — marked T02 complete.
- `.gsd/DECISIONS.md` — appended D012 gate payload persistence decision.
- `.gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md` — task execution summary.
