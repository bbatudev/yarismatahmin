---
estimated_steps: 4
estimated_files: 4
---

# T03: Final proof and M002 closure

**Slice:** S04 — Policy-Gated Final Integration
**Milestone:** M002

## Description

S04 runtime kanıtını alır; slice closure ve milestone summary dokümantasyonlarını tamamlar.

## Steps

1. S04 smoke run çalıştır.
2. Policy gate artifact + metadata mirror assert et.
3. T03/S04 summary dosyalarını yaz.
4. M002-SUMMARY + roadmap/project/state güncellemelerini tamamla.

## Must-Haves

- [x] `policy_gate_report.json` smoke run’da üretilmeli.
- [x] M002 milestone closure artifact’ları tamamlanmalı.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s04_policy_gate_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m002_s04_policy_gate_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); pg=pathlib.Path(md['stage_outputs']['artifact']['policy_gate']['report_json']); assert pg.exists(); print(run.name)"`

## Inputs

- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — artifact payload mirror.
- `mania_pipeline/artifacts/runs/<run_id>/policy_gate_report.json` — final integration proof.

## Expected Output

- `.gsd/milestones/M002/slices/S04/tasks/T03-SUMMARY.md` — runtime verification record.
- `.gsd/milestones/M002/slices/S04/S04-SUMMARY.md` — slice closure.
- `.gsd/milestones/M002/M002-SUMMARY.md` — milestone closure.
