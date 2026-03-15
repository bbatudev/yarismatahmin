---
id: S04
parent: M001
milestone: M001
provides:
  - Eval stage now emits canonical calibration artifacts (`calibration_bins.csv`, `calibration_report.json`) and embeds split/gender calibration summary into `eval_report.json` + `run_metadata.json`.
requires:
  - slice: S03
    provides: Unified Men/Women train payload (`model_path` + `feature_snapshot.feature_columns`) and stable eval stage contract.
affects:
  - S06
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py
  - mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/PROJECT.md
  - .gsd/STATE.md
key_decisions:
  - D018: Calibration contract breaks (model/feature mismatch) are fail-fast; sparse states remain non-fatal with explicit reasons.
  - D019: CLI tests must lock `CANONICAL_STAGES` before monkeypatching and keep calibration under `stage_outputs.eval_report.calibration`.
patterns_established:
  - Calibration is computed by rescoring canonical split data inside `stage_eval_report` (no new stage), preserving lifecycle topology.
  - Contract tests assert topology first, then payload wiring, to prevent monkeypatch masking.
observability_surfaces:
  - mania_pipeline/artifacts/runs/<run_id>/calibration_bins.csv
  - mania_pipeline/artifacts/runs/<run_id>/calibration_report.json
  - mania_pipeline/artifacts/runs/<run_id>/eval_report.json (`calibration` block)
  - mania_pipeline/artifacts/runs/<run_id>/run_metadata.json (`stage_outputs.eval_report.calibration`)
  - mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl
  - pytest diagnostics: `feature_column_mismatch`, `empty_high_prob`
drill_down_paths:
  - .gsd/milestones/M001/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T02-SUMMARY.md
duration: 2h15m
verification_result: passed
completed_at: 2026-03-14T16:33:39+03:00
---

# S04: Calibration Layer + Overconfidence/Drift Reporting

**Canonical eval pipeline now produces machine-readable calibration bins + drift diagnostics for Men/Women across Train/Val/Test without changing stage topology.**

## What Happened

S04 shipped calibration as an eval-layer contract, not a new runtime stage. `stage_eval_report` reloads per-gender models from `stage_outputs.train.genders.*`, rescoring canonical feature outputs with persisted feature-column order. From that rescoring pass, the pipeline now writes:
- `calibration_bins.csv` with fixed bin schema,
- `calibration_report.json` with split/gender `ece`, `wmae`, and high-prob (`p>=0.8`) drift summary,
- `eval_report.json.calibration` and `run_metadata.json.stage_outputs.eval_report.calibration` wiring.

Failure semantics were hardened: model/feature contract breaks fail the stage immediately; sparse-but-expected situations (`split_empty`, `empty_high_prob_band`) are non-fatal and explicit. CLI contract tests were also tightened to lock declared canonical stage topology before monkeypatching, so calibration cannot accidentally become a hidden new stage.

## Verification

All S04 slice-plan checks were rerun and passed:

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s04_calibration_smoke` ✅
- `./venv/Scripts/python -c "import json, pathlib, pandas as pd; runs=pathlib.Path('mania_pipeline/artifacts/runs'); run=max(runs.iterdir(), key=lambda p:p.stat().st_mtime); rp=run/'calibration_report.json'; bp=run/'calibration_bins.csv'; ep=run/'eval_report.json'; assert rp.exists() and bp.exists() and ep.exists(); report=json.loads(rp.read_text(encoding='utf-8')); eval_report=json.loads(ep.read_text(encoding='utf-8')); bins=pd.read_csv(bp); assert {'gender','split','bin_left','bin_right','sample_count','pred_mean','actual_rate','gap'}.issubset(bins.columns); assert set(report['calibration_summary'].keys())=={'men','women'}; assert 'calibration' in eval_report; print('S04 contract ok:', run.name)"` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py -k "feature_column_mismatch or empty_high_prob"` ✅

Observability surface confirmation (artifacts + metadata + stage order) on retained canonical proof run `20260314T161222Z_s04_calibration_smoke` also passed.

## Requirements Advanced

- R005 — Men/Women ayrı izlerin kalibrasyon raporlarında da korunması sağlandı; downstream gate’ler için sinyal yüzeyi genişledi.
- R006 — Existing eval contract bozulmadan calibration payload eklendi; side-by-side metrics reporting continuity korundu.

## Requirements Validated

- R007 — Calibration bins CSV + ECE/W-MAE + high-prob overconfidence/drift summary canonical runtime’da artifact + eval wiring + diagnostic testlerle doğrulandı.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- `ece` ve `wmae` şu an aynı weighted absolute gap formülünden türetiliyor; S06’da gate eşikleri netleşirken metrik ayrımı/versioning gerekebilir.

## Follow-ups

- S06’da calibration degradation gate’i için eşik/policy açıkça version’lanmalı (`split_empty` ve `empty_high_prob_band` durumlarının fail/soft-fail kararı dahil).
- Stage event schema (`status=started/succeeded`) gate-side tooling’de canonical olarak belgelenmeli; `event=stage_started` varsayımı kullanılmamalı.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — calibration rescoring + artifact emission + eval metadata wiring.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — calibration contract + failure-path diagnostics.
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` — backward-compatible eval contract assertions.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — canonical stage-topology lock and calibration payload placement assertions.
- `.gsd/REQUIREMENTS.md` — R007 status moved to validated with S04 evidence.
- `.gsd/milestones/M001/M001-ROADMAP.md` — S04 marked complete.
- `.gsd/PROJECT.md` — current-state refresh for S04 completion.
- `.gsd/STATE.md` — active slice/phase/status refresh.

## Forward Intelligence

### What the next slice should know
- Calibration artifacts are now stable and cheap to consume from `run_metadata.stage_outputs.eval_report.calibration`; S06 should consume this payload directly instead of re-reading ad-hoc files.

### What's fragile
- Calibration summary semantics around sparse splits/high-prob emptiness are policy-sensitive — S06 gate logic can accidentally over-fail if these reasons aren’t explicitly handled.

### Authoritative diagnostics
- `calibration_report.json` + `stage_events.jsonl` + `run_metadata.json.stage_outputs.eval_report.calibration` together are the fastest trustworthy triage path.

### What assumptions changed
- “Calibration needs a separate stage” — not required; eval-stage embedding preserved topology and met contract requirements.
