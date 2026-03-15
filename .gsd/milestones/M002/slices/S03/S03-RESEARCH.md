# S03 — Research

**Date:** 2026-03-15

## Summary

S03’te hedef, mevcut governance/ablation çıktısını tek başına bırakmak yerine drift ve calibration policy sinyalleriyle birleştiren karar yüzeyi üretmek. En güvenli seam yine `stage_eval_report`: tüm kanıtlar bu noktada hazır (ablation groups, drift payload, calibration policy payload) ve yeni bir stage açmadan fusion report üretmek mümkün.

Fusion kuralı ilk iterasyonda deterministik ve reason-coded olmalı. Amaç “en iyi karar modeli” değil, S04 gate coupling için makine tarafından tüketilebilir bir karar kontratı üretmek. Bu yüzden decision/confidence/reason_codes/evidence_bundle yapısı, ileri tuning öncesi yeterli kontrol-düzeyi sağlıyor.

## Recommendation

`governance_decision_report.json` üret ve `stage_outputs.eval_report.governance_decision` altında mirror et. Kararı gender bazında üretip aggregate karar ekle; evidence bundle içinde ablation delta özeti + drift alert kodları + calibration policy sonucu birlikte dursun.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Evidence extraction from ablation | mevcut `ablation_report` payload yapısı | Zaten canonical sözleşme içinde; yeni veri toplama gerekmez |
| Drift/policy consumption | S01/S02 payload yüzeyleri | S03 sadece fusion yapmalı, upstream hesaplamaları tekrar etmemeli |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — S01/S02 rapor üretim akışı fusion report için aynı emission pattern’i sunuyor.
- `mania_pipeline/tests/test_run_pipeline_m002_s02_calibration_policy_contract.py` — yeni M002 contract test pattern’i.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — artifact required report listesi genişletme noktası.

## Constraints

- Topology aynı kalmalı; yeni canonical stage eklenmez.
- Decision output deterministik olmalı; aynı seed/input için karar sabit kalmalı.
- Fusion, upsteam metric hesaplarını yeniden train/score etmemeli.

## Common Pitfalls

- **Fusion ile policy’yı karıştırmak** — S03 karar üretir; S04’te gate behavior bağlanır.
- **Artifact contract atlaması** — yeni governance decision report required list’e girmezse S06/S07 testleri drift eder.

## Open Risks

- Confidence formülü heuristik; S04’te gate coupling sonrası tekrar kalibre edilmesi gerekebilir.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| ML pipeline contract design | gsd built-in process | available |

## Sources

- Fusion için gerekli kanıt yüzeyleri mevcut eval payload’tan çıkarıldı (source: `mania_pipeline/scripts/run_pipeline.py`).
- Required artifact senkronu S06/S07 fixture’larından doğrulandı (source: `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`).
