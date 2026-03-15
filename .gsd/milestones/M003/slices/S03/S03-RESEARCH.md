# S03 — Research

**Date:** 2026-03-15

## Summary

S03 hedefi, S02’de üretilen HPO sinyallerini eval yüzeyine taşıyarak baseline ile karşılaştırmalı model seçimi yapabilmekti. Burada kritik nokta stage topology’yi büyütmeden (`feature -> train -> eval_report -> artifact`) ensemble kararını machine-readable şekilde üretmek.

En düşük-risk yaklaşım, yeni bir training stage eklemek yerine `stage_eval_report` içinde candidate scoring seam’i kurmak oldu. Baseline olasılıkları zaten eval sırasında yeniden skorlandığı için HPO best override ile tek bir ek model retrain edilip `baseline`, `hpo_best`, `ensemble_weighted` adayları aynı metrik fonksiyonlarıyla kıyaslanabiliyor.

## Recommendation

Ensemble kararını `ensemble_report.json` + `stage_outputs.eval_report.ensemble` olarak persist et. Seçim kuralı deterministic olmalı: Val Brier en iyi aday seçilir; baseline dışı seçimin uygulanabilmesi için minimum iyileşme eşiği (`ENSEMBLE_MIN_VAL_IMPROVEMENT`) geçilmelidir.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Split bazlı olasılık metrikleri | `_score_probability_bundle` | Brier/LogLoss/AUC/kalibrasyon hesaplarını tek yerden tutar |
| HPO candidate kaynağı | `hpo_report.json` (S02) | Best override kararını yeniden üretmeden tüketir |
| Backward-compatible training call | `_train_with_optional_profile` | legacy/new train signature farklılıklarını izole eder |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py::stage_eval_report` — Eval artifact ve governance surfaces burada üretiliyor.
- `mania_pipeline/scripts/run_pipeline.py::_train_with_optional_profile` — kwargs uyumluluğu için güvenli train çağrı katmanı.
- `mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py` — HPO report contract referansı.

## Constraints

- Canonical stage topology değişmeyecek.
- Ensemble kararı deterministic olmalı (seed ve sabit weight grid).
- Report-first yaklaşımı korunmalı (artifact + metadata mirror).

## Common Pitfalls

- **HPO report path’ine güvenmeden direkt train payload kullanmak** — best override kaybı yaşatır.
- **Baseline dışı adayı eşik olmadan promote etmek** — küçük/noise iyileşmelerde gereksiz model churn üretir.

## Open Risks

- Baseline ve HPO probability shape uyuşmazlığı durumunda blend candidate düşebilir; reason-coded fail surface şart.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Pipeline contract extension | gsd built-in process | available |

## Sources

- Eval/report wiring contract and helper seams (source: `mania_pipeline/scripts/run_pipeline.py`).
- HPO payload/report contract (source: `mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py`).
