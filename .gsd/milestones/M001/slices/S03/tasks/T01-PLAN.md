---
estimated_steps: 4
estimated_files: 2
---

# T01: Refactor `03_lgbm_train.py` into unified split-metrics core for both genders

**Slice:** S03 — Unified Men/Women Eval Core + Single Execution Path Enforcement
**Milestone:** M001

## Description

`03_lgbm_train.py` bugün Train/Val/Test metriklerini hesaplıyor ama yalnızca test brier döndürüyor. Bu task script-first eğitim çekirdeğini contract seviyesine çıkarır: her gender için aynı fonksiyonla `metrics_by_split` ve `feature_snapshot` üretilir. Böylece R005/R006 için gerekli yapı canonical runtime’a taşınabilir.

## Steps

1. `03_lgbm_train.py` içinde split bazlı metrik hesaplamayı tek yardımcı fonksiyona ayır; Train/Val/Test için brier, logloss, auc üretsin.
2. `train_baseline` dönüşünü `(model, payload)` yap; payload alanlarına `gender`, `metrics_by_split`, `feature_snapshot` ve `best_iteration` ekle.
3. AUC tek-sınıf durumunda deterministik davranış tanımla (`auc=None`, `auc_reason` alanı) ve payload içinde açıkça taşı.
4. Yeni sözleşmeyi kilitleyen `test_lgbm_train_metrics_contract.py` testini yaz; canonical split etiketleri ve feature snapshot alanlarını assert et.

## Must-Haves

- [ ] Aynı çekirdek fonksiyon Men ve Women çağrılarında ortak metrik payload şeması döndürür.
- [ ] Payload en az `Train`, `Val`, `Test` splitlerini içerir; her splitte `brier`, `logloss`, `auc` anahtarları bulunur.
- [ ] `feature_snapshot` içinde `feature_columns` ve `feature_count` tutarlı şekilde yer alır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_lgbm_train_metrics_contract.py`
- Test içinde `metrics_by_split['Test']` varlığı ve canonical split etiketlerinden beslendiği assertion ile doğrulanır.

## Observability Impact

- Signals added/changed: `train_baseline` payload’ında split-metric map ve AUC reason alanı görünür hale gelir.
- How a future agent inspects this: `stage_outputs.train` persist edildiğinde doğrudan run metadata üzerinden split metrikleri okunabilir.
- Failure state exposed: AUC hesaplanamadığında sessiz geçmek yerine `auc_reason` ile neden açıkça görünür.

## Inputs

- `mania_pipeline/scripts/03_lgbm_train.py` — mevcut eğitim fonksiyonu ve dönüş imzası.
- `.gsd/milestones/M001/slices/S03/S03-RESEARCH.md` — unified metrics payload gereksinimi ve açık riskler.

## Expected Output

- `mania_pipeline/scripts/03_lgbm_train.py` — unified split-metrics payload dönen script-first eğitim çekirdeği.
- `mania_pipeline/tests/test_lgbm_train_metrics_contract.py` — payload şemasını ve split-metrics sözleşmesini kilitleyen test.
