# S04 — Research

**Date:** 2026-03-15

## Summary

S04 hedefi, S03’te üretilen governance decision surface’ini regression gate davranışına bağlamak ve milestone-level final integration proof almak. En düşük riskli yaklaşım, gate motorunu (`_evaluate_regression_gate`) policy-aware hale getirip, stage_artifact içinde yeni bir integration raporu (`policy_gate_report.json`) üretmek.

Bu aşamada yeni modelleme yapmaya gerek yok; mevcut snapshot’tan (`metrics`, `calibration`, `governance_decision`) gelen sinyallerle fail/warning/fallback davranışı belirlenebilir. Böylece karar katmanı ve gate katmanı arasında makine-okunur coupling oluşur.

## Recommendation

Regression gate’e policy fallback kuralı ekle: calibration degradation normalde fail olur, ancak `apply_calibration_policy` + yeterli confidence + pozitif calibration improvement sinyali varsa warning/fallback olarak raporlanır. Ayrıca stage_artifact içinde `policy_gate_report.json` yazarak final integration diagnostics yüzeyi oluştur.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Gate baseline delta logic | mevcut `_evaluate_regression_gate` Brier/calibration/AUC kontratı | Mevcut policy’ye incremental genişletme en güvenli yol |
| Run-level evidence transport | `stage_outputs` snapshot extraction pattern | Yeni data pipe kurmadan coupling yapılır |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — regression gate ve artifact manifest akışı.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — gate fail semantics contract testleri.
- `mania_pipeline/tests/test_run_pipeline_m002_s03_governance_decision_contract.py` — governance decision payload shape.

## Constraints

- Brier non-degradation kuralı blocking olmaya devam etmeli.
- Policy fallback sadece açık koşullarda devreye girmeli; gizli softening olmamalı.
- Canonical stage topology korunmalı.

## Common Pitfalls

- **Fallback’i aşırı genişletmek** — calibration degradation her durumda warning’e dönmemeli.
- **Diagnostics yüzeyi eksikliği** — fallback davranışı raporlanmazsa decision-gate coupling denetlenemez.

## Open Risks

- Fallback eşiği (confidence/improvement) erken iterasyonda konservatif kalabilir; historical tuning gerekebilir.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Pipeline gate policy design | gsd built-in process | available |

## Sources

- Regression gate mevcut davranışı koddan çıkarıldı (source: `mania_pipeline/scripts/run_pipeline.py`).
- Gate contract beklentileri S06 testlerinden doğrulandı (source: `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py`).
