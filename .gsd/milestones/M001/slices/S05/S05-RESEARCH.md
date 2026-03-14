# M001/S05 — Research

**Date:** 2026-03-14

## Summary

S05 bu milestone içinde doğrudan **R008 (Feature governance ledger)** ve **R009 (Controlled ablation reporting)** requirement’larını sahipleniyor; çıktıların S06’ya taşınacak gate kararlarına güvenilir veri sağlaması bekleniyor. Mevcut canonical run (`20260314T161222Z_s04_calibration_smoke`) `feature -> train -> eval_report -> artifact` sırasını stabil çalıştırıyor ve `stage_outputs.train.feature_snapshot` + `metrics_by_split` + `eval_report.calibration` yüzeylerini üretiyor; fakat governance/ablation için henüz hiçbir artifact veya metadata alanı yok.

S05 için en güçlü seam `stage_eval_report`: S04 calibration da burada stage-topology bozulmadan eklenmiş. Aynı pattern ile governance ledger + controlled ablation raporu eklenebilir. Kritik sınırlayıcı nokta: ablation için gerekli “feature çıkarılmış model metrikleri” baseline artifact’larda yok; ya eval aşamasında kontrollü yeniden eğitim yapılmalı ya da approximation kullanılmalı. R009’daki delta metrik seti (Brier/LogLoss/AUC/Calibration) nedeniyle en düşük-risk yaklaşım **subset retrain ablation**.

Araştırmadaki sürpriz: seed/logic feature grubunu çıkarma probe’u Val’da Women için iyileşme gösterirken Test’te belirgin kötüleşme üretiyor (ör. Women ΔVal Brier ≈ -0.0086 ama ΔTest Brier ≈ +0.0079). Tek split veya tek metrikle drop kararı verilirse yanlış pozitif risk yüksek. Governance kararı multi-evidence + split-aware olmak zorunda.

## Recommendation

S05’i **eval-report katmanında governance+ablation extension** olarak uygula (yeni stage ekleme):

1. `stage_eval_report` içinde mevcut train payload’dan (`genders.*.model_path`, `feature_snapshot.feature_columns`, `metrics_by_split`) baseline evidence üret.
2. Feature ledger için deterministic grup sınıflandırması ekle (isim-konvansiyonu + explicit map): her feature için `feature`, `group`, `default_action`, `evidence` alanı doldur.
3. “Suspicious group” listesini baseline evidence ile otomatik seç (örn. iki cinsiyette de düşük/0 importance yoğunluğu veya drift-riskli logic grupları).
4. Seçilen gruplar için **controlled subset retrain** yap: ilgili kolonları düşür, `train_baseline(..., random_state=context['seed'])` ile Men/Women yeniden eğit, Val/Test için ΔBrier/ΔLogLoss/ΔAUC + ΔCalibration (ECE/W-MAE + high-prob gap) hesapla.
5. Run klasörüne en az şu artifact’ları yaz:
   - `governance_ledger.csv` (zorunlu alanlar: `feature, group, default_action, evidence`)
   - `ablation_report.json` (grup bazlı delta şeması)
6. `eval_report.json` ve `run_metadata.json.stage_outputs.eval_report` içine `governance` payload’ını ekle (path + özet), stage order’ı değiştirme.

Neden bu yol: S03/S04 kontratıyla uyumlu, R008/R009’u machine-readable artifact’a bağlar, S06 regression gate’in tüketebileceği net delta yüzeyi üretir.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Feature etkisini modelden bağımsız ve scorer-aware ölçmek | `sklearn.inspection.permutation_importance` | Fitted model + custom scoring ile güvenilir importance/delta sinyali verir; elle shuffle döngüsü yazma riskini azaltır. |
| Brier tabanlı scorer üretimi | `sklearn.metrics.make_scorer(..., response_method='predict_proba', greater_is_better=False)` + `brier_score_loss` | Probability metric’lerinde scorer semantiğini doğru ve tekrar kullanılabilir kurar. |
| LightGBM önem tipleri (split/gain) | LightGBM built-in feature importance (`feature_importances_`, `feature_importance`) | Governance evidence’ı modelin native importance sinyaline dayandırır; custom importance hesaplarıyla drift yaratmaz. |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — Canonical stage topology sabit (`feature`, `train`, `eval_report`, `artifact`); S05 bunu bozmadan `eval_report` çıktısını genişletmeli.
- `mania_pipeline/scripts/run_pipeline.py::stage_eval_report` — S04 calibration burada üretildi; governance+ablation için aynı artifact-emission pattern’i kullanılmalı.
- `mania_pipeline/scripts/run_pipeline.py::_build_calibration_rows_and_summary` — Split/gender calibration hesap helper’ı hazır; ablation calibration delta’sı için tekrar kullanılabilir.
- `mania_pipeline/scripts/03_lgbm_train.py::train_baseline` — DataFrame’deki mevcut feature set ile eğitiyor; ablation için kolon düşürülmüş DataFrame vererek subset retrain yapılabilir (imza değiştirmeden).
- `mania_pipeline/scripts/split_leakage_contracts.py` — Feature namespace kontratı (`*_diff` + explicit non-diff allowlist) governance grup sınıflandırması için güvenilir başlangıç seti veriyor.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — Stage topology lock testi var; governance ayrı stage’e taşınırsa kırılır.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — Eval-stage artifact contract test pattern’i S05 için doğrudan şablon.
- `mania_pipeline/scripts/analyze_weak_features.py` — Korelasyon tabanlı ad-hoc analiz var ama hard-coded path + run-contract dışı; canonical governance için referans değil, sadece fikir kaynağı.

## Constraints

- Canonical stage order değişemez; S05 çıktıları mevcut stage’lerden birine (pratikte `eval_report`) bağlanmalı.
- R008 ledger alanları zorunlu: en az `feature`, `group`, `default_action`, `evidence`.
- R009 delta raporu multi-metric olmalı: ΔBrier, ΔLogLoss, ΔAUC, ΔCalibration.
- Men/Women feature namespace birebir aynı değil (`men_only`: `CoachTenureYears_diff`, `FTr_diff`, `MasseyPct_diff`, `MasseyAvgRank_diff`, `ProgramAge_diff`); grup/ablation hesapları gender-aware olmalı.
- Val split örnek sayısı düşük (134); yalnız Val’a bakarak `default_action=drop` kararı kırılgan.
- Runtime maliyeti grup sayısıyla lineer artar; S04 kanıt run’ında `train` aşaması ~2.4s (iki gender). Kontrollü group sayısı sınırı gerekli.

## Common Pitfalls

- **Tek metrikle karar** — Sadece Brier veya sadece importance ile drop kararı verme; R009 çoklu delil istiyor.
- **Val/Test çelişkisini görmezden gelme** — Probe’da aynı ablation Women için Val’da iyi, Test’te kötü; split-aware karar zorunlu.
- **Gender farkını flatten etmek** — Men-only feature’ları Women ledger’a zorla yazmak yanlış evidence üretir.
- **Eval stage’i model artifact çöplüğüne çevirmek** — Ablation modellerini kalıcı `.pkl` olarak yazmak gereksiz; delta için in-memory eğitim yeterli.

## Open Risks

- `default_action` eşikleri (keep/drop/candidate) yanlış kalibre edilirse governance otomasyonu ya çok agresif ya çok pasif kalabilir.
- Çok sayıda suspicious group seçilirse runtime hızla uzar ve S06 reproducibility akışını zorlar.
- Calibration delta (özellikle high-prob band) düşük örnekli splitlerde gürültülü olabilir; minimum sample guard gerekebilir.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LightGBM | `tondevrel/scientific-agent-skills@xgboost-lightgbm` | available (not installed) — `npx skills add tondevrel/scientific-agent-skills@xgboost-lightgbm` |
| scikit-learn | `davila7/claude-code-templates@scikit-learn` | available (not installed) — `npx skills add davila7/claude-code-templates@scikit-learn` |
| Kaggle workflow | `shepsci/kaggle-skill@kaggle` | available (not installed) — `npx skills add shepsci/kaggle-skill@kaggle` |
| Python performance | `python-performance-optimization` | installed (available_skills list) |

## Sources

- S05 currently owns R008/R009 and must emit governance + ablation artifacts (source: [`.gsd/REQUIREMENTS.md`](../../../../REQUIREMENTS.md)).
- Canonical stage order is locked and must remain `feature/train/eval_report/artifact` (source: [`mania_pipeline/tests/test_run_pipeline_cli.py`](../../../../../mania_pipeline/tests/test_run_pipeline_cli.py)).
- Existing eval stage already emits calibration artifacts and has reusable split/gender scoring helpers (source: [`mania_pipeline/scripts/run_pipeline.py`](../../../../../mania_pipeline/scripts/run_pipeline.py)).
- Train payload already provides `feature_snapshot` + split metrics and supports subset retrain via dropped columns (source: [`mania_pipeline/scripts/03_lgbm_train.py`](../../../../../mania_pipeline/scripts/03_lgbm_train.py)).
- Latest canonical run has no governance artifact yet and shows Men/Women feature-count asymmetry (source: [`mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/run_metadata.json`](../../../../../mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/run_metadata.json)).
- Stage duration profile (`feature` dominant, `train` cheap) from canonical run events guides controlled ablation scope (source: [`mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/stage_events.jsonl`](../../../../../mania_pipeline/artifacts/runs/20260314T161222Z_s04_calibration_smoke/stage_events.jsonl)).
- Probe ablation (seed/logic group) showed Val/Test conflict, confirming multi-evidence requirement (source: local command output, 2026-03-14, `./venv/Scripts/python` ablation probe).
- Permutation importance API contract and scorer options (source: [scikit-learn permutation_importance docs](https://scikit-learn.org/dev/modules/generated/sklearn.inspection.permutation_importance)).
- `make_scorer` with `response_method='predict_proba'` and Brier scoring semantics (source: [scikit-learn model evaluation docs](https://scikit-learn.org/dev/modules/model_evaluation.html)).
- LightGBM feature-importance type guidance (split vs gain) (source: [LightGBM Parameters.rst](https://github.com/microsoft/lightgbm/blob/master/docs/Parameters.rst)).
