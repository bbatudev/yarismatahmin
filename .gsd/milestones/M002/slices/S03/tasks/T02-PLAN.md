---
estimated_steps: 5
estimated_files: 3
---

# T02: Wire decision report and artifact requirement

**Slice:** S03 — Governance Decision Fusion (Ablation + Drift + Calibration)
**Milestone:** M002

## Description

Yeni governance decision report’unu eval output’a bağlar ve artifact contract required listesine ekler; S06/S07 fixture’larını günceller.

## Steps

1. `governance_decision_report.json` artifact yazımını ekle.
2. `eval_report` payload’ına `governance_decision` bloğunu ekle.
3. Artifact required paths’e `governance_decision_report_json` ekle.
4. S06/S07 fixture context’lerinde decision report path’i ekle.
5. Contract testlerini çalıştır.

## Must-Haves

- [x] Decision report artifact required listede zorunlu.
- [x] S06/S07 fixture testleri yeni required path ile geçer.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — eval/artifact wiring.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — artifact contract fixture.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — submission contract fixture.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — wiring + required artifact update.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — fixture sync.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — fixture sync.
