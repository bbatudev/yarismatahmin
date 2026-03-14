---
estimated_steps: 4
estimated_files: 6
---

# T03: Wire governance outputs into canonical eval surface and prove runtime contract

**Slice:** S05 — Feature Governance + Controlled Ablation
**Milestone:** M001

## Description

S05 çıktılarının canonical tüketim yüzeylerine bağlandığını doğrular: `eval_report.json` ve `run_metadata.json` governance artifact path/özetlerini taşır, stage topology korunur ve gerçek runtime smoke ile contract kapanır.

## Steps

1. `stage_eval_report` dönüş payload’ına `governance` blokunu ekle (`artifacts`, `summary`, `diagnostics`) ve mevcut calibration alanını bozmadan JSON genişlet.
2. CLI/topology lock testlerini güncellemeden koru; governance wiring için dedicated orchestrator contract testlerini tamamla.
3. Slice verification test setini çalıştırıp regressionsız geçtiğini doğrula.
4. Canonical smoke run çalıştır; son run üzerinde script assertion ile governance artifact varlığı + metadata/eval wiring + stage order invariants’ı doğrula.

## Must-Haves

- [ ] `eval_report.json.governance` ve `run_metadata.json.stage_outputs.eval_report.governance` aynı artifact path’leri ve summary sayaçlarını taşır.
- [ ] Canonical stage listesi değişmeden kalır (`feature`, `train`, `eval_report`, `artifact`).
- [ ] Slice verification komutları ve smoke run birlikte geçtiğinde demo koşulu sağlanır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s05_governance_smoke`
- `./venv/Scripts/python -c "import json, pathlib; runs=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s05_governance_smoke')); assert runs; run=runs[-1]; md=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); er=json.loads((run/'eval_report.json').read_text(encoding='utf-8')); assert md['stage_outputs']['eval_report']['governance']['artifacts']['ledger_csv']==er['governance']['artifacts']['ledger_csv']; assert tuple(md['stage_order'])==('feature','train','eval_report','artifact'); print('ok', run.name)"`

## Observability Impact

- Signals added/changed: eval stage çıktısında governance summary sayaçları ve diagnostics listesi.
- How a future agent inspects this: tek noktadan `run_metadata.json.stage_outputs.eval_report.governance` + artifact dosyaları.
- Failure state exposed: governance artifact path eksikliği, boş executed group seti, topology drift assertion failure.

## Inputs

- `.gsd/milestones/M001/slices/S05/tasks/T02-PLAN.md` — ablation report schema ve summary alanları.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — stage topology lock contract.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — eval_report calibration compat contract.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — governance payload runtime wiring.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — slice-level integration assertions.
- `mania_pipeline/artifacts/runs/<run_id>/eval_report.json` — governance block.
- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — stage_outputs governance block.
