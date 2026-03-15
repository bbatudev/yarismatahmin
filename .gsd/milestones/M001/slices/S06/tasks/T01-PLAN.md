---
estimated_steps: 4
estimated_files: 2
---

# T01: Add artifact contract report and required-file enforcement in artifact stage

**Slice:** S06 — Artifact Contract + Reproducibility + Regression Gate
**Milestone:** M001

## Description

Artifact stage’e required artifact haritası eklenir; her dosya için existence bilgisi raporlanır ve eksik dosya durumunda stage fail edilir.

## Steps

1. `stage_artifact` içinde required artifact path map oluştur.
2. `artifact_contract_report.json` yaz ve `missing_artifacts` listesini üret.
3. Manifest içine contract status/ref ekle.
4. Missing artifact varsa RuntimeError ile fail et.

## Must-Haves

- [x] Contract raporu required artifact setini machine-readable verir.
- [x] Eksik artifact durumda deterministic fail reason üretilir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py -k "contract"`

## Observability Impact

- Signals added/changed: `stage_outputs.artifact.artifact_contract.status`
- How a future agent inspects this: `artifact_contract_report.json` + `run_metadata.json`
- Failure state exposed: `missing_artifacts` listesi

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — mevcut artifact manifest emission logic
- `.gsd/milestones/M001/slices/S06/S06-RESEARCH.md` — artifact contract seam kararı

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — artifact contract emission + fail enforcement
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — contract assertions
