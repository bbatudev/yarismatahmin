---
estimated_steps: 6
estimated_files: 2
---

# T01: Policy-aware regression fallback

**Slice:** S04 — Policy-Gated Final Integration
**Milestone:** M002

## Description

Regression gate değerlendirmesine governance decision sinyalini bağlayarak kontrollü fallback/warning davranışı ekler.

## Steps

1. Snapshot extraction’a governance decision sinyalini ekle.
2. Regression gate içinde policy decision/confidence/improvement sinyallerini oku.
3. Calibration degradation durumunda fallback koşulunu uygula.
4. Fallback/warning sinyallerini report payload’a yaz.
5. Policy fallback davranışını test ile doğrula.
6. Blocking semantics’in brier tarafında korunmasını kontrol et.

## Must-Haves

- [x] Fallback sadece açık koşullarda çalışır.
- [x] Blocking failure semantiği korunur.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — regression gate current implementation.
- `.gsd/milestones/M002/slices/S03/S03-SUMMARY.md` — governance decision contract.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — policy-aware regression logic.
- `mania_pipeline/tests/test_run_pipeline_m002_s04_policy_gate_contract.py` — fallback contract proof.
