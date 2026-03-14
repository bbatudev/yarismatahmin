---
id: S02
parent: M001
milestone: M001
provides:
  - Deterministic split and leakage gate enforcement inside canonical `feature` stage with fail-fast blocking before train
  - Persisted per-gender gate diagnostics at `run_metadata.json -> stage_outputs.feature.gates.{men,women}`
requires:
  - slice: S01
    provides: Canonical stage lifecycle wrapper and run-scoped metadata/event artifact contract
affects:
  - S03
  - S07
key_files:
  - mania_pipeline/scripts/split_leakage_contracts.py
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_split_leakage_contracts.py
  - mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - mania_pipeline/artifacts/runs/<run_id>/run_metadata.json
  - mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/PROJECT.md
  - .gsd/STATE.md
key_decisions:
  - D011: Leakage validator uses exact forbidden-column set + explicit namespace allowlist (no keyword heuristics)
  - D012: Persist canonical aggregate gate payload under `stage_outputs.feature.gates.{men,women}` with nested split/leakage evidence
patterns_established:
  - Shared gate-result schema (`pass`, `blocking_rule`, `reason`, `evidence`) across split and leakage contracts
  - Feature-stage gate wrapper composes split+leakage results per gender and raises on first blocking rule
observability_surfaces:
  - `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` (`stage_outputs.feature.gates.{men,women}`)
  - `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl` (`feature` failed event includes `blocking_rule` in `error.message`)
  - `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py -k "fail" -vv`
  - `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke`
drill_down_paths:
  - .gsd/milestones/M001/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md
duration: 2h20m
verification_result: passed
completed_at: 2026-03-14T18:02:16+03:00
---

# S02: Split/Leakage Contract Gates

**Shipped fail-fast split/leakage contract gates in canonical runtime, with machine-readable gate diagnostics persisted per gender.**

## What Happened

T01 introduced standalone validators in `split_leakage_contracts.py` and locked deterministic payload shape with unit tests. Split checks now enforce authority from `02_feature_engineering.py::assign_split` and fail on season-label mismatch or unknown split label. Leakage checks fail on forbidden post-game/raw columns and required namespace contract violations.

T02 wired these validators into `run_pipeline.py::stage_feature` immediately after men/women dataframe generation. If any gender fails, pipeline raises `RuntimeError` containing the `blocking_rule`, halts in `feature`, and returns non-zero. If both pass, canonical gate payloads are written under `stage_outputs.feature.gates.{men,women}` without changing S01 stage order.

The slice now satisfies the S02 demo: split/leakage violations stop canonical execution before training, while pass-path evidence is persisted for downstream consumers.

## Verification

Executed all S02 plan checks:

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py` → **4 passed**
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_cli.py` → **5 passed**
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py -k "fail" -vv` → **1 passed** (`feature` fail-fast with `blocking_rule` assertion)
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke` → **passed**
- `./venv/Scripts/python -c "... gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass'] ..."` → **passed** (`S02 gate metadata contract ok`)

Observability confirmation:

- Pass-path metadata confirmed in the latest `*_s02_split_leakage_smoke` run under `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` with populated `stage_outputs.feature.gates.{men,women}` including nested split/leakage evidence.
- Failure-path diagnostics confirmed via fail-fast integration test and an executed forced-fail runtime check where `stage_events.jsonl` contained only `feature started/failed`, `failed_stage=feature`, and `error.message` included `R004_LEAKAGE_FORBIDDEN_COLUMNS`.

## Requirements Advanced

- R003 — Split authority now resolves from script-side `assign_split`, reducing notebook/script drift risk ahead of S03 single execution path enforcement.

## Requirements Validated

- R002 — Deterministic walk-forward split contract is now enforced and verified by unit + integration + real-runtime metadata evidence.
- R004 — Leakage guardrails now fail fast in canonical runtime and expose machine-readable blocking diagnostics.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- Split validator intentionally does not enforce season contiguity; it enforces authoritative season→label mapping and unknown-label rejection.
- Gate checks are embedded in `feature` stage (by design, D010); there is still no dedicated standalone gate stage.
- S03 single execution path enforcement is still pending.

## Follow-ups

- In S03, treat `stage_outputs.feature.gates` pass state as a hard precondition for unified Men/Women eval path.
- Add explicit script/notebook training-path enforcement to close R003/R019 fully.

## Files Created/Modified

- `mania_pipeline/scripts/split_leakage_contracts.py` — Deterministic split/leakage validators and shared gate payload builder.
- `mania_pipeline/scripts/run_pipeline.py` — Feature-stage gate wiring, fail-fast `RuntimeError`, and gate metadata persistence.
- `mania_pipeline/tests/test_split_leakage_contracts.py` — Unit lock for split/leakage pass/fail payload contracts.
- `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` — CLI integration tests for fail-fast blocking and pass-path persistence.
- `.gsd/REQUIREMENTS.md` — Moved R002 and R004 to Validated with S02 proof evidence.
- `.gsd/milestones/M001/M001-ROADMAP.md` — Marked S02 complete.
- `.gsd/milestones/M001/slices/S02/S02-SUMMARY.md` — Slice-level compressed summary.
- `.gsd/milestones/M001/slices/S02/S02-UAT.md` — Concrete UAT script for split/leakage gates.
- `.gsd/PROJECT.md` — Refreshed project current state with S02 completion.
- `.gsd/STATE.md` — Advanced slice/state to S02 complete and S03 next.

## Forward Intelligence

### What the next slice should know
- `stage_outputs.feature.gates.{men,women}` is now stable and already includes nested split/leakage evidence, so S03 can consume one canonical payload instead of re-checking raw columns.
- Failure diagnosis is easiest from `stage_events.jsonl` because the surfaced `blocking_rule` is in the failed `feature` event message.

### What's fragile
- Gate validators assume canonical columns (`Season`, `Split`, `TeamA`, `TeamB`, `Target`) remain present post-feature engineering — schema drift here will block runs early.
- Leakage namespace allowlist is explicit by design (D011); intentional feature-schema changes require synchronized validator updates.

### Authoritative diagnostics
- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — source of truth for pass-path gate payloads and persisted evidence.
- `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl` — source of truth for fail-fast stage stop and blocking rule diagnostics.
- `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` — fastest regression detector for gate wiring + stage-order guarantees.

### What assumptions changed
- “Split/leakage checks are only planned validations” — now false; they are runtime-enforced canonical gates.
- “Gate outcomes are only visible in test output” — now false; outcomes are persisted in run metadata for downstream slices.
