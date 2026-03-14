# S02 — Research

**Date:** 2026-03-15

## Summary

S01 ile profile seam hazırlandığı için S02’de odak, reproducible HPO harness’i canonical train stage içine eklemek. Burada kritik hedef “en iyi modeli bulmak” değil, aday denemeleri ve seçim sonucunu machine-readable şekilde kayıt altına almak.

HPO maliyeti yüksek olabileceği için default davranış değişmemeli: `--hpo-trials 0` olduğunda mevcut hızlı akış korunmalı. HPO aktif olduğunda (`>0`) deterministic trial parametreleri üretilmeli ve gender bazlı sonuçlar aynı şemada raporlanmalı.

## Recommendation

`stage_train` içinde deterministic parameter-trial üretimi + trial evaluation + winner selection ekle. Çıktıyı her run’da `hpo_report.json` olarak yaz; trials=0 durumunda `status=skipped` raporu üretmeye devam et.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Training invocation compatibility | S01’de eklenen profile-aware train call + fallback pattern | Eski test stub’ları bozmadan yeni kwargs geçişi sağlar |
| Metric extraction | mevcut `metrics_by_split` payload contract | HPO scoring için yeni hesaplama altyapısı gerektirmez |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py::stage_train` — profile propagation seam.
- `mania_pipeline/scripts/03_lgbm_train.py::train_baseline` — profile+payload üretimi.
- `mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py` — M003 test pattern referansı.

## Constraints

- Canonical stage topology değişmeyecek.
- HPO defaultta kapalı kalmalı (`--hpo-trials 0`).
- Trial üretimi seed’e bağlı deterministik olmalı.

## Common Pitfalls

- **HPO’yu default açık yapmak** — runtime maliyetini gereksiz yükseltir.
- **Report yazmamak** — deneme geçmişi ve seçim gerekçesi kaybolur.

## Open Risks

- Küçük trial sayısında gerçek kalite artışı garanti değil; S03’de model-seçim katmanı bunu ele alacak.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Reproducible search harness | gsd built-in process | available |

## Sources

- Train payload seam from S01 implementation (source: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/scripts/03_lgbm_train.py`).
