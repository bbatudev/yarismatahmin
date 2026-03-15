---
estimated_steps: 3
estimated_files: 3
---

# T03: Prove runtime drift contract and update S01 artifacts

**Slice:** S01 — Regime Drift Baseline & Signal Contract
**Milestone:** M002

## Description

Drift-enabled canonical smoke run ile gerçek runtime kanıtı alınıp S01 plan/summary güncellenir.

## Steps

1. Drift smoke run çalıştır.
2. Drift artifact/payload assert script’i çalıştır.
3. Task/slice summary dosyalarını yaz.

## Must-Haves

- [x] Runtime’da drift report oluşur ve metadata’ya bağlanır.
- [x] S01 closure dokümantasyonu güncel olur.

## Verification

- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label m002_s01_drift_smoke`
- `./venv/Scripts/python -c "... drift contract assert ..."`

## Inputs

- `.gsd/milestones/M002/slices/S01/S01-PLAN.md`
- `mania_pipeline/artifacts/runs/<run_id>/drift_regime_report.json`

## Expected Output

- `.gsd/milestones/M002/slices/S01/tasks/T03-SUMMARY.md`
- `.gsd/milestones/M002/slices/S01/S01-SUMMARY.md`
