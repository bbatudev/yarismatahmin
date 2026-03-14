# S01: Training Profile Contract (Baseline vs Quality v1)

**Goal:** Canonical train stage’i profile-aware hale getirip model geliştirme yolunu kontrollü profile kontratıyla başlatmak.
**Demo:** `run_pipeline.py --training-profile quality_v1` çalıştığında train payload ve metadata içinde profile bilgisi persist edilir; baseline default bozulmaz.

## Must-Haves

- CLI `--training-profile {baseline,quality_v1}` desteği.
- `03_lgbm_train.py::train_baseline` profile argümanı alır ve deterministic param map kullanır.
- `stage_outputs.train.genders.{men,women}` profile bilgisini taşır.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py -q`
- `./venv/Scripts/python -m pytest mania_pipeline/tests -q`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --run-label m003_s01_profile_smoke`
- `./venv/Scripts/python -c "import json,pathlib; run=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_m003_s01_profile_smoke'))[-1]; md=json.loads((run/'run_metadata.json').read_text()); tr=md['stage_outputs']['train']; assert tr['training_profile']=='quality_v1'; assert tr['genders']['men']['training_profile']=='quality_v1'; print('M003/S01 training profile contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.train.training_profile`
- Inspection surfaces: `run_metadata.json.stage_outputs.train.genders.<gender>.training_profile`
- Failure visibility: unknown profile için train stage fail-fast hata mesajı.
- Redaction constraints: no secret/PII

## Integration Closure

- Upstream surfaces consumed: existing feature gates + canonical train payload schema.
- New wiring introduced in this slice: CLI/context → stage_train → train_baseline profile propagation.
- What remains before the milestone is truly usable end-to-end: S02 HPO harness + S03 ensemble + S04 submission readiness gate.

## Tasks

- [x] **T01: Add named training profiles to baseline trainer** `est:40m`
  - Why: Model değişimini kontrollü profile sözleşmesine bağlamak.
  - Files: `mania_pipeline/scripts/03_lgbm_train.py`
  - Do: baseline param setini profile haritasına taşı; `quality_v1` profile ekle; payload’a profile metadata yaz.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py -k "profiles" -q`
  - Done when: trainer profile seçimini deterministic şekilde uygular.

- [x] **T02: Wire training profile through canonical orchestrator** `est:35m`
  - Why: Profile seçimi runtime entrypoint’ten yönetilmeli.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py`
  - Do: CLI arg + context propagation + stage_train payload wiring ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py -q`
  - Done when: run metadata train payload’ında profile görünür.

- [x] **T03: Runtime proof and S01 closure artifacts** `est:30m`
  - Why: Kontratın gerçek canonical run’da doğrulanması gerekli.
  - Files: `.gsd/milestones/M003/slices/S01/S01-SUMMARY.md`, `.gsd/milestones/M003/slices/S01/tasks/T03-SUMMARY.md`, `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`
  - Do: quality profile smoke run al, assert script çalıştır, docs’u kapat.
  - Verify: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --training-profile quality_v1 --run-label m003_s01_profile_smoke`
  - Done when: runtime profile propagation kanıtlandı.

## Files Likely Touched

- `mania_pipeline/scripts/03_lgbm_train.py`
- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m003_s01_training_profile_contract.py`
