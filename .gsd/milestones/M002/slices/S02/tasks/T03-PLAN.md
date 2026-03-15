---
estimated_steps: 4
estimated_files: 3
---

# T03: Runtime proof and S02 closure artifacts

**Slice:** S02 — Regime-Aware Calibration Policy Engine
**Milestone:** M002

## Description

Canonical smoke run ile policy contract’ın gerçek runtime’da üretildiğini doğrular; sonuçları task/slice summary dosyalarına geçirir.

## Steps

1. Policy-enabled canonical smoke run çalıştır.
2. Run metadata üzerinden policy payload mirror assert et.
3. T03 summary dosyasını runtime kanıtıyla yaz.
4. S02 slice summary ve roadmap/requirement/state güncellemelerini tamamla.

## Must-Haves

- [x] Runtime proof komutu başarılı olmalı.
- [x] `calibration_policy_report.json` dosyası ve metadata mirror doğrulanmalı.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s02_policy_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m002_s02_policy_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); p=md['stage_outputs']['eval_report']['calibration_policy']; rpt=pathlib.Path(p['report_json']); assert rpt.exists(); print(run.name)"`

## Inputs

- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — stage output mirror proof.
- `mania_pipeline/artifacts/runs/<run_id>/calibration_policy_report.json` — artifact proof.

## Expected Output

- `.gsd/milestones/M002/slices/S02/tasks/T03-SUMMARY.md` — runtime verification record.
- `.gsd/milestones/M002/slices/S02/S02-SUMMARY.md` — slice closure.
- `.gsd/milestones/M002/M002-ROADMAP.md` — S02 completion state.
