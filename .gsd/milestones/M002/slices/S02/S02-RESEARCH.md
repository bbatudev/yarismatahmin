# S02 — Research

**Date:** 2026-03-15

## Summary

S01 ile drift yüzeyi hazır olduğu için S02’de en düşük riskli seam, policy motorunu `stage_eval_report` içinde kurmak. Böylece canonical topology (`feature -> train -> eval_report -> artifact`) değişmeden kalıyor ve policy çıktısı aynı eval payload yüzeyinden downstream slice’lara aktarılabiliyor.

Policy seçimi için ilk iterasyonda deterministik kural gerekli: aday yöntemler (`none`, `platt`, `isotonic`) Val split üzerinde aynı scoring sözleşmesiyle karşılaştırılmalı, ancak düşük örnekli/tek-sınıflı Val durumunda yöntemler reason-coded şekilde unavailable işaretlenmeli. S01 drift rejim sinyali bu seçime tie-break/fallback davranışı verecek şekilde tüketilmeli.

## Recommendation

Regime-aware calibration selector’ı eval stage içinde ayrı helper’larla kur: aday üretimi + availability reason + metrik değerlendirme + deterministik seçim. Çıktıyı `calibration_policy_report.json` olarak persist et ve `stage_outputs.eval_report.calibration_policy` altında mirror et.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Probability calibration transform | `sklearn` IsotonicRegression + LogisticRegression (Platt-style) | Güvenilir ve battle-tested; custom calibrator riski yok |
| ECE/WMAE summary | mevcut `_build_calibration_rows_and_summary` helper’ı | S04 calibration sözleşmesiyle tutarlı metrik yüzeyi korunur |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — eval artifact emission pattern (`calibration`, `drift`, `governance`) S02 için doğrudan genişletilebilir.
- `mania_pipeline/tests/test_run_pipeline_m002_s01_drift_contract.py` — M002 slice contract test stili, S02 testine baz olur.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — artifact stage required artifact fixture yapısı; yeni report eklendiğinde güncellenmeli.

## Constraints

- Canonical stage topology değişmeyecek; yeni stage eklenmeyecek.
- Policy kararı deterministik olmalı (seed sabitliğinde aynı input -> aynı method).
- Low-sample ve single-class Val durumda fail değil, reason-coded unavailable behavior beklenir.

## Common Pitfalls

- **Policy availability ile selection’ı karıştırmak** — unavailable yöntemleri selection pool’dan çıkarıp reason’ı payload’da tut.
- **Artifact contract drift** — eval payload’a yeni report bağlandıysa S06/S07 fixture’larını da senkron güncelle.

## Open Risks

- Val örnek sayısı sınırında method seçimi çoğu durumda `none` kalabilir; bu davranış S03 policy tuning’de yeniden ayarlanabilir.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Python pipeline contracts | gsd built-in process | available |

## Sources

- Eval payload/contract pattern mevcut koddan çıkarıldı (source: `mania_pipeline/scripts/run_pipeline.py`).
- Artifact required-surface davranışı S06 testlerinden çıkarıldı (source: `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`).
