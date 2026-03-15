# S01 — Research

**Date:** 2026-03-15

## Summary

M003’e düşük riskli giriş için en doğru seam, canonical akışta train stage’i profile-aware yapmak: `baseline` davranışını korurken yeni bir `quality_v1` profile eklemek. Böylece model değişikliği kontrollü ve geri alınabilir olur; aynı zamanda S02 HPO için resmi bir profile kontratı oluşur.

Bu adımda HPO yapmıyoruz; sadece profile seçimi, train payload’ına profile metadata’sı, ve CLI/context wiring’i ekliyoruz. Böylece M003’te model iyileştirme zinciri “parametre deneme” yerine “kontratlı profile” üzerinden ilerliyor.

## Recommendation

`03_lgbm_train.py` içinde named training profiles tanımla, `train_baseline(..., profile=...)` imzasını genişlet, `run_pipeline.py` üzerinden `--training-profile` argümanını train stage’e geçir. Default `baseline` kalsın.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Canonical runtime wiring | mevcut `run_pipeline.py::stage_train` contract pattern | Yeni profile behavior’ı mevcut contract üstünden risksiz ekler |
| Payload persistence | mevcut `stage_outputs.train.genders.*` yapısı | Profile metadata için yeni storage layer gerektirmez |

## Existing Code and Patterns

- `mania_pipeline/scripts/03_lgbm_train.py` — fixed param baseline trainer; profile seam buraya eklenmeli.
- `mania_pipeline/scripts/run_pipeline.py` — CLI/context/train wiring için canonical nokta.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — topology lock + CLI contract referansı.

## Constraints

- Default behavior (`baseline`) değişmemeli.
- Canonical stage topology değişmeyecek.
- Profile seçim hataları deterministic fail-fast olmalı.

## Common Pitfalls

- **Default profile drift** — baseline parametreleri istemeden değişirse geçmiş run karşılaştırması bozulur.
- **Profile bilgisini persist etmemek** — hangi modelin hangi profile ile üretildiği kaybolur.

## Open Risks

- `quality_v1` profile ilk iterasyonda baseline’dan daha iyi olmayabilir; bu normal ve S02 HPO ile çözülecek.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Python ML pipeline evolution | gsd built-in process | available |

## Sources

- Training seam ve payload alanları koddan çıkarıldı (source: `mania_pipeline/scripts/03_lgbm_train.py`, `mania_pipeline/scripts/run_pipeline.py`).
