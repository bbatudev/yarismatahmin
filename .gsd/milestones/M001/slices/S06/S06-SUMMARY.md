---
id: S06
parent: M001
milestone: M001
provides:
  - Artifact contract enforcement + reproducibility gate + regression gate reports wired into canonical artifact stage.
requires:
  - slice: S04
    provides: Calibration summary payload in `stage_outputs.eval_report.calibration.calibration_summary`.
  - slice: S05
    provides: Governance and ablation artifacts already wired under `stage_outputs.eval_report.governance`.
affects:
  - S07
key_files:
  - mania_pipeline/scripts/run_pipeline.py
  - mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M001/M001-ROADMAP.md
  - .gsd/PROJECT.md
  - .gsd/STATE.md
key_decisions:
  - D024: Keep artifact/repro/regression checks inside `stage_artifact` with report-first + fail-fast semantics.
patterns_established:
  - Stage-artifact policy gate pattern: write machine-readable report, then enforce blocking failures.
  - Snapshot-from-stage_outputs pattern for run-to-run metric comparisons.
observability_surfaces:
  - mania_pipeline/artifacts/runs/<run_id>/artifact_contract_report.json
  - mania_pipeline/artifacts/runs/<run_id>/reproducibility_report.json
  - mania_pipeline/artifacts/runs/<run_id>/regression_gate_report.json
  - mania_pipeline/artifacts/runs/<run_id>/artifact_manifest.json (`contracts` block)
  - run_metadata.json (`stage_outputs.artifact.{artifact_contract,reproducibility,regression_gate}`)
drill_down_paths:
  - .gsd/milestones/M001/slices/S06/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S06/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S06/tasks/T03-SUMMARY.md
duration: ~2h20m
verification_result: passed
completed_at: 2026-03-15
---

# S06: Artifact Contract + Reproducibility + Regression Gate

**Canonical artifact stage now enforces required artifact integrity, same commit+seed reproducibility tolerance, and previous-run regression policy with explicit pass/fail/skip diagnostics.**

## What Happened

S06 added a new contract layer inside `stage_artifact` without changing stage topology:
- **Artifact contract report** validates required run artifacts and fails stage when mandatory files are missing.
- **Reproducibility gate** looks up the latest successful same commit+seed baseline and enforces `|ΔTest Brier|<=1e-4` per gender.
- **Regression gate** compares against the latest successful prior run and enforces policy:
  - Brier mandatory non-degradation (blocking)
  - Calibration degradation fail (blocking)
  - AUC informational (non-blocking)

All gate outcomes are persisted as JSON reports and mirrored in `stage_outputs.artifact` and `artifact_manifest.json.contracts`.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` ✅
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_feature_governance_ledger.py mania_pipeline/tests/test_feature_governance_ablation.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -q` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_contract_smoke` ✅
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s06_repro_check` ✅
- Runtime assertions on latest run reports (artifact contract pass, reproducibility pass, regression pass/skip domain) ✅

## Requirements Advanced

- R012 — S07’ye kalan submission doğrulaması için artifact/gate yüzeyleri stabilize edildi.

## Requirements Validated

- R010 — Required artifact contract report ve fail-fast enforcement runtime/test ile doğrulandı.
- R011 — Same commit+seed reproducibility tolerance gate runtime’da pass/skip/fail semantics ile doğrulandı.
- R018 — Previous-run regression gate policy runtime ve contract testleriyle doğrulandı.

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none

## Known Limitations

- İlk defa koşulan branch/commit kombinasyonlarında reproducibility baseline olmadığı için gate doğal olarak `skipped` döner.

## Follow-ups

- S07’de submission validator raporunu `stage_outputs.artifact` yüzeyine aynı contract pattern’iyle bağla.
- S06 gate raporlarını S07 final acceptance script’inde tek noktadan assert et.

## Files Created/Modified

- `mania_pipeline/scripts/run_pipeline.py` — artifact/repro/regression gate evaluators + report emission + enforcement.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — S06 gate contract coverage.
- `.gsd/REQUIREMENTS.md` — R010/R011/R018 validated durumuna geçirildi.
- `.gsd/milestones/M001/M001-ROADMAP.md` — S06 completed.
- `.gsd/PROJECT.md` — current state refreshed.
- `.gsd/STATE.md` — active slice/task handoff moved to S07.

## Forward Intelligence

### What the next slice should know
- Submission tarafı için gerekli kalite/güvenlik kapıları artık artifact stage’de hazır; S07 bunları tüketerek final acceptance yazmalı.

### What's fragile
- Regression baseline seçimi “en son başarılı run” kuralına bağlı; yanlış run temizliği yapılırsa karşılaştırma anlamı kayabilir.

### Authoritative diagnostics
- `run_metadata.json.stage_outputs.artifact` hızlı triage yüzeyi; detay için üç rapor JSON’u authoritative.

### What assumptions changed
- “Regression/repro gate için ayrı stage gerekir” — gerekmedi; artifact stage içinde report-first + fail-fast modeli yeterli oldu.
