---
estimated_steps: 6
estimated_files: 1
---

# T01: Readiness evaluator and artifact wiring

**Slice:** S04 — Submission Readiness Final Gate
**Milestone:** M003

## Description

Artifact stage’e readiness fusion helper’ı ekler; report-first davranışıyla fail path’te de readiness artifact persist edilir.

## Steps

1. Readiness helper fonksiyonunu tanımla.
2. Artifact/repro/regression/policy/submission/ensemble payload’larını fuse et.
3. Submission pre-blocker akışını düzenle.
4. Fail raise’lerden önce readiness report yaz.
5. Manifest/return payload’a readiness yüzeyi ekle.
6. Kontrat testlerini çalıştır.

## Must-Haves

- [x] Fail path’te readiness dosyası kalıcı olarak yazılır.
- [x] Stage return payload `readiness` alanını içerir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s04_submission_readiness_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — existing artifact gate logic.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — readiness helper + wiring.
