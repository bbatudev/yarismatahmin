# S04 — Research

**Date:** 2026-03-15

## Summary

S04’ün hedefi, mevcut gate yüzeylerini (artifact/repro/regression/policy/submission/ensemble) tek bir release-readiness kararında birleştirmek. Burada ana risk, mevcut fail-fast davranışını bozarken readiness observability kazanmaya çalışmak.

En düşük-risk çözüm, `stage_artifact` içinde yeni bir readiness değerlendirme helper’ı eklemek ve `submission_readiness_report.json` üretmek oldu. Böylece stage fail etse bile (ör. regression gate) readiness raporu önce yazılıp diagnosability korunuyor.

## Recommendation

`stage_artifact` içinde submission üretiminden önce blocker durumlarını derle, readiness raporunu her durumda persist et, ardından mevcut fail-fast raise sırasını koru. Böylece hem backward-compatibility hem de release kararı görünürlüğü korunur.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Gate sonuçlarının üretimi | mevcut `artifact_contract`, `reproducibility`, `regression`, `policy_gate` payload’ları | Readiness için yeni metrik üretmek yerine mevcut contract’ları fuse eder |
| Submission validation | `_build_optional_submission` | `ID,Pred` strict doğrulama zaten burada merkezi |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py::stage_artifact` — S04 için doğal fusion noktası.
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — submission yüzeyi fixture pattern’i.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — stage_artifact contract fixture pattern’i.

## Constraints

- Regression/Brier hard fail semantiği korunmalı.
- Submission hala opsiyonel; readiness ise bunun durumunu açıkça kodlamalı.

## Common Pitfalls

- **Readiness raporunu sadece pass run’da yazmak** — fail path diagnosability kaybı.
- **Submission failure’da readiness üretmeden exception fırlatmak** — release sebebi izlenemez.

## Open Risks

- İlk run’larda baseline yokluğu sebebiyle readiness `caution` üretmesi beklenen bir durum; release otomasyonunda yanlış alarm diye yorumlanmamalı.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Gate fusion & diagnostics | gsd built-in process | available |

## Sources

- Artifact stage and gate semantics (source: `mania_pipeline/scripts/run_pipeline.py`).
- Existing contract fixture patterns (source: `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`, `...s07_submission_contract.py`).
