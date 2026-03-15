# S07: Optional Submission Validation + Final Integration

**Goal:** Optional submission üretimini canonical pipeline’a bağlayıp `ID,Pred` formatını strict doğrulamak ve M001 final integration kanıtını tamamlamak.
**Demo:** `run_pipeline.py --submission-stage stage2` çalışınca `submission_stage2.csv` + `submission_validation_report.json` üretilir; `stage_outputs.artifact.submission` ve `artifact_manifest.json.contracts.submission` bu çıktıları taşır; invalid schema/range durumunda stage fail olur.

## Must-Haves

- Submission generation opsiyonel (`none` default) ve stage seçimi (`stage1|stage2`) parametreyle kontrol edilir (R012).
- Üretilen dosya strict `ID,Pred` schema + null/range kontrollerinden geçer; başarısızlıkta fail-fast olur.
- Final integration run’ında S06 gate’leri + submission validation birlikte pass verir.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s07_submission_smoke --submission-stage stage2`
- `./venv/Scripts/python -c "import json,pathlib,pandas as pd; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s07_submission_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); sub=md['stage_outputs']['artifact']['submission']; assert sub['status']=='passed'; df=pd.read_csv(sub['submission_csv']); assert list(df.columns)==['ID','Pred']; assert df['Pred'].between(0,1).all(); print('S07 submission contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.artifact.submission.status`
- Inspection surfaces: `submission_validation_report.json`, `submission_<stage>.csv`, `artifact_manifest.json.contracts.submission`
- Failure visibility: validation report içindeki check map (`columns_exact`, `id_non_null`, `pred_non_null`, `pred_in_range`)
- Redaction constraints: submission dosyası sadece `ID` ve numeric `Pred` içerir; secret yok.

## Integration Closure

- Upstream surfaces consumed: S06 artifact contract/gate pipeline + Kaggle sample submission CSV’leri.
- New wiring introduced in this slice: artifact stage optional submission branch (`--submission-stage`).
- What remains before the milestone is truly usable end-to-end: nothing (M001 closure).

## Tasks

- [x] **T01: Add optional submission stage argument and builder flow in artifact stage** `est:45m`
  - Why: Submission davranışının opsiyonel/parametrik olması canonical default run’u bozmadan R012’yi açar.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
  - Do: `--submission-stage` argümanı ekle; `none|stage1|stage2` seçiminde artifact stage’e submission builder branch’i bağla.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -k "skips"`
  - Done when: Submission istenmediğinde deterministic skip report üretiliyor.

- [x] **T02: Implement strict submission validator and fail-fast semantics** `est:45m`
  - Why: R012 format güvenliği için schema/range/null kontrolleri deterministic olmalı.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
  - Do: `ID,Pred` exact schema, `Pred` numeric range `[0,1]`, null check’lerini validator’da enforce et; failde stage error üret.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
  - Done when: Submission validation report pass/fail durumunu açıkça taşıyor ve fail path enforce ediliyor.

- [x] **T03: Prove final integration runtime with submission enabled and update milestone state** `est:45m`
  - Why: M001 final assembly sadece test değil gerçek runtime + artifact sözleşmesiyle kapanmalı.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `.gsd/REQUIREMENTS.md`, `.gsd/milestones/M001/M001-ROADMAP.md`, `.gsd/milestones/M001/slices/S07/S07-SUMMARY.md`
  - Do: submission-enabled smoke run al; stage_outputs/manifest/submission artifacts assert et; requirement/roadmap/project/state dosyalarını milestone closure’a güncelle.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s07_submission_smoke --submission-stage stage2`
  - Done when: Runtime’da submission pass ve M001’de kalan requirement kalmıyor.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py`
- `.gsd/REQUIREMENTS.md`
- `.gsd/milestones/M001/M001-ROADMAP.md`
- `.gsd/milestones/M001/slices/S07/S07-PLAN.md`
