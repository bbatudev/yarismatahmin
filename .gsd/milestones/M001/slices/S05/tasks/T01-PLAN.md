---
estimated_steps: 4
estimated_files: 4
---

# T01: Build governance ledger contract from canonical train payload

**Slice:** S05 — Feature Governance + Controlled Ablation
**Milestone:** M001

## Description

Canonical train payload’ından (feature snapshot + split metrics + model importance) deterministic governance ledger üretimini kurar. Bu görev R008’in zorunlu artifact sözleşmesini kapatır ve T02 ablation seçim logic’i için güvenilir giriş sağlar.

## Steps

1. `feature_governance.py` içinde feature grouping ve ledger row builder helper’larını tanımla; Men-only kolonları women tarafında zorla üretmeme kuralını uygula.
2. `default_action` policy’sini (`keep|drop|candidate`) baseline evidence’tan deterministic türet; evidence alanını machine-readable (JSON string) tut.
3. `run_pipeline.py::stage_eval_report` içine ledger üretim çağrısını ve `governance_ledger.csv` yazımını ekle (henüz ablation yok).
4. Ledger schema ve value-domain için `test_feature_governance_ledger.py` + minimal orchestrator wiring assertion’ı yaz.

## Must-Haves

- [ ] Ledger CSV her satırda `feature`, `group`, `default_action`, `evidence` alanlarını zorunlu taşır.
- [ ] `default_action` sadece `keep`, `drop`, `candidate` değerlerinden birini alır.
- [ ] Gender namespace farkı yanlış satır üretmeden handle edilir (men-only feature women evidence’a yazılmaz).

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py -k ledger`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — mevcut `stage_eval_report` ve calibration emission pattern’i.
- `mania_pipeline/scripts/03_lgbm_train.py` — `feature_snapshot` + split metrics payload contract’ı.
- `.gsd/milestones/M001/slices/S05/S05-RESEARCH.md` — ledger zorunlu alanları ve gender-aware constraints.

## Expected Output

- `mania_pipeline/scripts/feature_governance.py` — ledger üretim helper’ları.
- `mania_pipeline/scripts/run_pipeline.py` — ledger artifact emission wiring.
- `mania_pipeline/tests/test_feature_governance_ledger.py` — ledger schema/domain testleri.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — ledger wiring assertion (slice-level contract başlangıcı).
