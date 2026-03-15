---
estimated_steps: 4
estimated_files: 3
---

# T03: Runtime proof and S03 closure

**Slice:** S03 — Governance Decision Fusion (Ablation + Drift + Calibration)
**Milestone:** M002

## Description

Canonical smoke run ile governance decision contract’ını canlıda doğrular, ardından S03 ve global docs closure güncellemelerini yapar.

## Steps

1. S03 smoke run çalıştır.
2. Metadata’dan governance decision payload mirror assert et.
3. T03 summary dosyasını runtime kanıtıyla yaz.
4. S03 summary + roadmap/state/decision güncellemelerini tamamla.

## Must-Haves

- [x] `governance_decision_report.json` gerçek run’da üretilmeli.
- [x] Metadata mirror assert’i geçmeli.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s03_decision_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m002_s03_decision_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); gd=md['stage_outputs']['eval_report']['governance_decision']; assert pathlib.Path(gd['report_json']).exists(); print(run.name)"`

## Inputs

- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — decision payload mirror.
- `mania_pipeline/artifacts/runs/<run_id>/governance_decision_report.json` — artifact proof.

## Expected Output

- `.gsd/milestones/M002/slices/S03/tasks/T03-SUMMARY.md` — runtime verification record.
- `.gsd/milestones/M002/slices/S03/S03-SUMMARY.md` — slice closure.
- `.gsd/milestones/M002/M002-ROADMAP.md` — S03 completion state.
