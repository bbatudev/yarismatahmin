---
estimated_steps: 6
estimated_files: 2
---

# T01: Governance decision fusion helpers

**Slice:** S03 — Governance Decision Fusion (Ablation + Drift + Calibration)
**Milestone:** M002

## Description

Ablation, drift ve calibration policy sinyallerini gender-level governance decision yapısında birleştiren helper’ları uygular.

## Steps

1. Ablation evidence extraction helper’ını ekle.
2. Drift alert/test gap extraction helper’ını ekle.
3. Calibration policy selected/default/improvement extraction helper’ını ekle.
4. Gender decision + confidence + reason_codes üret.
5. Aggregate decision logic ekle.
6. Contract test dosyası ile payload şemasını doğrula.

## Must-Haves

- [x] Gender payload `decision/confidence/reason_codes/evidence_bundle` alanlarını içerir.
- [x] Aggregate decision deterministic setten seçilir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — existing eval signals.
- `.gsd/milestones/M002/slices/S02/S02-SUMMARY.md` — policy payload contract.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — fusion helper implementation.
- `mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py` — decision contract tests.
