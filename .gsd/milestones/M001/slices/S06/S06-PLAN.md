# S06: Artifact Contract + Reproducibility + Regression Gate

**Goal:** Canonical run için artifact bütünlüğünü, same commit+seed tekrar üretilebilirliği ve önceki run’a karşı çoklu-kural regression kararını machine-readable raporlarla otomatik enforce etmek.
**Demo:** `run_pipeline.py` çalışınca `artifact_contract_report.json`, `reproducibility_report.json`, `regression_gate_report.json` üretilir; `run_metadata.json.stage_outputs.artifact` bu raporları/kararları taşır; gate fail durumunda run stage-level fail olur.

## Must-Haves

- Artifact contract required dosyaları var/yok olarak raporlar ve eksikte fail verir (R010).
- Reproducibility gate aynı commit+seed koşusunda `|ΔBrier|<=1e-4` kuralını uygular; breach fail verir (R011).
- Regression gate önceki başarılı run’a göre Brier mandatory + calibration degradation fail + AUC informational kuralıyla pass/fail üretir (R018).

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_feature_governance_ledger.py mania_pipeline/tests/test_feature_governance_ablation.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_contract_smoke`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_repro_check`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s06_repro_check'))[-1]; rep=json.loads((run/'reproducibility_report.json').read_text()); assert rep['status']=='passed'; print('repro ok', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.artifact.{artifact_contract,reproducibility,regression_gate}.status`
- Inspection surfaces: run dizinindeki üç rapor + `artifact_manifest.json` + `run_metadata.json`
- Failure visibility: `missing_artifacts`, `reproducibility.failures`, `regression_gate.blocking_failures`
- Redaction constraints: raporlar sadece aggregate metric/gate state taşır; secret/row-level prediction içermez.

## Integration Closure

- Upstream surfaces consumed: `stage_outputs.train.metrics_by_split`, `stage_outputs.eval_report.calibration.calibration_summary`, governance/calibration artifact path’leri.
- New wiring introduced in this slice: `stage_artifact` içinde contract+gate hesaplama, rapor emission ve fail-fast karar mekanizması.
- What remains before the milestone is truly usable end-to-end: S07 optional submission validation + final integration.

## Tasks

- [x] **T01: Add artifact contract report and required-file enforcement in artifact stage** `est:1h`
  - Why: R010’un “zorunlu artifact seti” koşulu machine-readable ve fail-fast enforce edilmeden audit güvenilir olmaz.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
  - Do: `stage_artifact` içinde required artifact map çıkar; var/yok raporu yaz (`artifact_contract_report.json`); eksik artifact’ta stage fail üret.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -k "contract"`
  - Done when: Contract raporu her run’da oluşuyor ve eksik dosya durumunda deterministic fail reason üretiyor.

- [x] **T02: Implement reproducibility tolerance gate with same commit+seed baseline lookup** `est:1h`
  - Why: R011 aynı kod+seed için ölçülebilir stabilite ister; drift sessiz kalmamalı.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
  - Do: prior successful run metadata’dan same commit+seed baseline bul; Test Brier delta’yı `|Δ|<=1e-4` kuralıyla değerlendir; raporu yaz ve breach’te fail et.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_repro_check`
  - Done when: baseline varsa `reproducibility_report.json.status` pass/fail üretir, yoksa reason-coded skip verir.

- [x] **T03: Implement previous-run regression gate and wire statuses into manifest/metadata** `est:1h`
  - Why: R018 çoklu-kural kalite kapısı olmadan kalite düşüşleri sessiz geçer.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`, `mania_pipeline/artifacts/runs/<run_id>/artifact_manifest.json`
  - Do: önceki başarılı run’a karşı Brier/calibration/AUC delta kararını üret; `regression_gate_report.json` yaz; blocking failure’da stage fail et; status’leri manifest+stage output’a yansıt.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
  - Done when: `stage_outputs.artifact.regression_gate.status` her run’da mevcut ve policy’ye göre pass/fail/skip döner.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`
- `.gsd/REQUIREMENTS.md`
- `.gsd/milestones/M001/M001-ROADMAP.md`
- `.gsd/milestones/M001/slices/S06/S06-PLAN.md`
