---
id: T02
parent: S04
milestone: M001
provides:
  - Locked CLI stage-topology contract against hidden regressions and proved S04 calibration wiring on a real canonical run (`20260314T161222Z_s04_calibration_smoke`).
key_files:
  - mania_pipeline/tests/test_run_pipeline_cli.py
  - .gsd/milestones/M001/slices/S04/tasks/T02-PLAN.md
  - .gsd/milestones/M001/slices/S04/S04-PLAN.md
  - .gsd/DECISIONS.md
key_decisions:
  - Added D019: CLI contract tests must assert module-declared canonical stage list before monkeypatching handlers; calibration remains eval_report payload, not a stage.
patterns_established:
  - In lifecycle tests that monkeypatch stage handlers, first assert declared runtime topology (`CANONICAL_STAGES`) so test doubles cannot hide stage-order drift.
observability_surfaces:
  - mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/calibration_bins.csv
  - mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/calibration_report.json
  - mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/eval_report.json
  - mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/run_metadata.json
  - mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/stage_events.jsonl
duration: 55m
verification_result: passed
completed_at: 2026-03-14T16:36:00+03:00
blocker_discovered: false
---

# T02: Prove end-to-end S04 contract on canonical run and lock CLI compatibility

**CLI contract testi artık monkeypatch maskelenmesine karşı stage topology’yi doğrudan kilitliyor; canonical smoke run’da calibration artifacts + eval wiring + men/women split coverage uçtan uca doğrulandı.**

## What Happened

- `mania_pipeline/tests/test_run_pipeline_cli.py` güncellendi:
  - Yeni test eklendi: `test_cli_canonical_stage_topology_remains_locked` (`CANONICAL_STAGES == ('feature','train','eval_report','artifact')`).
  - Stubbed `eval_report` stage çıktısı calibration payload ile zenginleştirildi (`bins_csv`, `report_json`) ve bunun `stage_outputs.eval_report` altında kaldığı assert edildi.
  - Başarılı run senaryosunda `metadata['stage_outputs']` anahtar sırası canonical stage sırasına kilitlendi; `calibration` adında ayrı stage olmadığı explicit doğrulandı.
- Pre-flight gereği `.gsd/milestones/M001/slices/S04/tasks/T02-PLAN.md` içine `## Observability Impact` eklendi.
- Canonical smoke run çalıştırıldı: `20260314T161222Z_s04_calibration_smoke`.
- Run-level assertion komutlarıyla `calibration_bins.csv`, `calibration_report.json`, `eval_report.json.calibration` ve men/women + Train/Val/Test coverage doğrulandı.
- S04 planında T02 tamamlandı olarak işaretlendi.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s04_calibration_smoke` ✅
- `./venv/Scripts/python -c "import json, pathlib, pandas as pd; runs=pathlib.Path('mania_pipeline/artifacts/runs'); run=max(runs.iterdir(), key=lambda p:p.stat().st_mtime); bins=pd.read_csv(run/'calibration_bins.csv'); rep=json.loads((run/'calibration_report.json').read_text(encoding='utf-8')); er=json.loads((run/'eval_report.json').read_text(encoding='utf-8')); assert set(bins['gender'])=={'men','women'}; assert set(bins['split'])=={'Train','Val','Test'}; assert set(rep['calibration_summary'].keys())=={'men','women'}; assert 'calibration' in er; print('S04 e2e ok', run.name)"` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py` ✅
- `./venv/Scripts/python -c "import json, pathlib, pandas as pd; runs=pathlib.Path('mania_pipeline/artifacts/runs'); run=max(runs.iterdir(), key=lambda p:p.stat().st_mtime); rp=run/'calibration_report.json'; bp=run/'calibration_bins.csv'; ep=run/'eval_report.json'; assert rp.exists() and bp.exists() and ep.exists(); report=json.loads(rp.read_text(encoding='utf-8')); eval_report=json.loads(ep.read_text(encoding='utf-8')); bins=pd.read_csv(bp); assert {'gender','split','bin_left','bin_right','sample_count','pred_mean','actual_rate','gap'}.issubset(bins.columns); assert set(report['calibration_summary'].keys())=={'men','women'}; assert 'calibration' in eval_report; print('S04 contract ok:', run.name)"` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py -k "feature_column_mismatch or empty_high_prob"` ✅
- `./venv/Scripts/python -c "import json, pathlib; runs=pathlib.Path('mania_pipeline/artifacts/runs'); run=max(runs.iterdir(), key=lambda p:p.stat().st_mtime); rep=json.loads((run/'calibration_report.json').read_text(encoding='utf-8')); expected={'Train','Val','Test'}; summary=rep['calibration_summary']; assert set(summary)=={'men','women'}; assert set(summary['men'])==expected; assert set(summary['women'])==expected; print('coverage ok', run.name)"` ✅

## Diagnostics

- Canonical proof run: `mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/`
  - `calibration_bins.csv`: split/gender bin-level calibration rows.
  - `calibration_report.json`: split/gender `ece`, `wmae`, high-prob band diagnostics.
  - `eval_report.json`: top-level `calibration` wiring.
  - `run_metadata.json`: `stage_outputs.eval_report.calibration` payload.
  - `stage_events.jsonl`: unchanged lifecycle order (`feature -> train -> eval_report -> artifact`).
- Regression signal now explicit in tests:
  - Stage topology drift (new/reordered stage) fails `test_cli_canonical_stage_topology_remains_locked` and/or canonical stage order assertions.
  - Calibration being extracted as a separate stage (instead of eval payload) fails CLI metadata assertions.

## Deviations

- None.

## Known Issues

- None.

## Files Created/Modified

- `mania_pipeline/tests/test_run_pipeline_cli.py` — locked declared stage topology and validated calibration stays under eval_report payload.
- `.gsd/milestones/M001/slices/S04/tasks/T02-PLAN.md` — added required `## Observability Impact` section (pre-flight fix).
- `.gsd/milestones/M001/slices/S04/S04-PLAN.md` — marked T02 complete.
- `.gsd/DECISIONS.md` — appended D019 for topology-lock test strategy.
- `.gsd/milestones/M001/slices/S04/tasks/T02-SUMMARY.md` — this execution summary.
