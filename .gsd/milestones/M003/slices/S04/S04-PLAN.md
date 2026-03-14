# S04: Submission Readiness Final Gate

**Goal:** Release kararını tek bir machine-readable readiness contract’ında üretmek.
**Demo:** `stage_artifact` sonunda `submission_readiness_report.json` yazılır ve `stage_outputs.artifact.readiness` altında `ready|caution|blocked` sinyali görünür.

## Must-Haves

- `submission_readiness_report.json` her run’da (pass/fail path dahil) üretilir.
- Artifact stage return payload’ında `readiness` surface’i bulunur.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile baseline --hpo-trials 0 --submission-stage none --run-label m003_s04_readiness_base --artifacts-root mania_pipeline/artifacts/runs_m003/s04_gate`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile baseline --hpo-trials 0 --submission-stage stage2 --run-label m003_s04_readiness_gate --artifacts-root mania_pipeline/artifacts/runs_m003/s04_gate`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs_m003/s04_gate').glob('*_m003_s04_readiness_gate'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); rpt=pathlib.Path(md['stage_outputs']['artifact']['readiness']['report_json']); data=json.loads(rpt.read_text()); assert data['checks']['submission']['status']=='passed'; print(data['status'])"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.artifact.readiness.status`
- Inspection surfaces: `submission_readiness_report.json`
- Failure visibility: `blocking_checks`, `warnings`, per-check status map
- Redaction constraints: only aggregate decision signals, no secret output.

## Integration Closure

- Upstream surfaces consumed: artifact/repro/regression/policy/submission/ensemble outputs.
- New wiring introduced in this slice: artifact-stage readiness fusion surface.
- What remains before the milestone is truly usable end-to-end: M003 milestone closure docs only.

## Tasks

- [x] **T01: Add readiness evaluation helper and artifact-stage wiring** `est:45m`
  - Why: S04’ün ana deliverable’ı readiness fusion logic.
  - Files: `mania_pipeline/scripts/run_pipeline.py`
  - Do: readiness helper ekle, submission/build error path’lerinde de report-first davranışını koru.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py -q`
  - Done when: `readiness.report_json` stage output’ta bulunur ve fail path’te de dosya persist olur.

- [x] **T02: Add S04 readiness contract tests** `est:35m`
  - Why: ready/caution/blocked decision semantics’i contract seviyesinde kilitlemek.
  - Files: `mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py`
  - Do: caution (submission none), ready (submission pass + gates pass), blocked (gate fail) senaryolarını test et.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py -q`
  - Done when: üç karar yolu deterministic olarak assert edilir.

- [x] **T03: Runtime readiness proof and milestone closure updates** `est:30m`
  - Why: gerçek canonical run ile readiness kararı doğrulanmalı.
  - Files: `.gsd/milestones/M003/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M003/M003-SUMMARY.md`
  - Do: izolasyonlu root ile base+gate run al, readiness assert yap, closure docs yaz.
  - Verify: two-run proof commands in Verification section.
  - Done when: runtime’da readiness=ready yolu kanıtlanır ve M003 closure tamamlanır.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py`
