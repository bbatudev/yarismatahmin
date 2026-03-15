---
estimated_steps: 5
estimated_files: 5
---

# T02: Implement controlled ablation retrain and delta report schema

**Slice:** S05 — Feature Governance + Controlled Ablation
**Milestone:** M001

## Description

Şüpheli feature grupları için kontrollü subset retrain akışını ekler ve R009’un zorunlu çoklu-delta raporunu üretir. Bu görev tek metrik/tek split yanlış karar riskini düşürmek için Val+Test ve calibration delta’larını aynı artifact’ta birleştirir.

## Steps

1. Ledger çıktısından suspicious group seçimini deterministic hale getir (priority + max group cap + seed-stable ordering).
2. Her grup için gender-aware drop-column seti oluştur; uygun kolon yoksa skip reason yaz.
3. `train_baseline(..., random_state=seed)` ile group-drop retrain çalıştır; Val/Test baseline’a karşı ΔBrier, ΔLogLoss, ΔAUC hesapla.
4. Mevcut calibration helper’ını tekrar kullanarak ΔECE, ΔWMAE ve high-prob gap delta’larını hesapla; sample-guard reason’larını taşı.
5. `ablation_report.json` şemasını finalize et ve contract testlerini yaz.

## Must-Haves

- [ ] Ablation raporu her çalıştırılan grup için `delta_brier`, `delta_logloss`, `delta_auc`, `delta_calibration` alanlarını içerir.
- [ ] Split/gender bazlı çalıştırılamayan durumlar explicit reason code ile raporlanır.
- [ ] Ablation çalışma seti deterministic ve runtime maliyeti kontrollü (max-group cap) olur.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ablation.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py -k ablation`

## Observability Impact

- Signals added/changed: `governance.summary.executed_group_count`, `skipped_groups`, group-level reason codes.
- How a future agent inspects this: run dizinindeki `ablation_report.json` ve `run_metadata.json.stage_outputs.eval_report.governance`.
- Failure state exposed: her group/gender/split için skip/failure reason (`group_missing`, `no_gender_features`, `split_empty`, `empty_high_prob_band`).

## Inputs

- `.gsd/milestones/M001/slices/S05/tasks/T01-PLAN.md` — ledger schema ve grouping/output varsayımları.
- `mania_pipeline/scripts/feature_governance.py` — T01’de eklenecek ledger builder seam’i.
- `mania_pipeline/scripts/03_lgbm_train.py` — retrain fonksiyonu ve metric payload contract’ı.
- `mania_pipeline/scripts/run_pipeline.py` — calibration helper ve eval stage artifact emission akışı.

## Expected Output

- `mania_pipeline/scripts/feature_governance.py` — ablation runner + delta calculators.
- `mania_pipeline/scripts/run_pipeline.py` — ablation artifact emission wiring.
- `mania_pipeline/tests/test_feature_governance_ablation.py` — ablation delta schema/determinism testleri.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — ablation metadata wiring assertions.
