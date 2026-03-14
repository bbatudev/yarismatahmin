# M004 Başlangıç Referansı (Mevcut Başarı Ölçütü Testi)

**Tarih:** 2026-03-15
**Kaynak run:** `mania_pipeline/artifacts/runs_m003/s04_gate/20260314T233640Z_m003_s04_readiness_gate`

## 1) Test Suite Sonucu

- Komut: `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- Sonuç: **55 passed**

## 2) Mevcut Model Başarı Göstergeleri (Referans)

- Men Test Brier: **0.18175050076078456**
- Women Test Brier: **0.14223205049047852**
- Men Test LogLoss: **0.5381222738302219**
- Women Test LogLoss: **0.44633879320997155**
- Men Test AUC: **0.8022388059701493**
- Women Test AUC: **0.8927378035197148**

## 3) Release Hazırlık Durumu

- Readiness Status: **ready**
- Submission Status: **passed**
- Submission Stage: **stage2**

## Not

Bu dosya M004 boyunca "önce/sonra" kıyaslarında referans alınacak başlangıç noktasıdır.
