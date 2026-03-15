---
estimated_steps: 3
estimated_files: 2
---

# T01: Add optional submission stage argument and builder flow in artifact stage

**Slice:** S07 — Optional Submission Validation + Final Integration
**Milestone:** M001

## Description

CLI’ye `--submission-stage` parametresi eklenir ve artifact stage’de optional submission builder branch’i aktive edilir.

## Steps

1. `parse_args` içine `--submission-stage` (`none|stage1|stage2`) ekle.
2. Context’e `submission_stage` geçir.
3. Artifact stage’de optional submission flow’u çağır.

## Must-Haves

- [x] Varsayılan davranış (`none`) mevcut run akışını bozmaz.
- [x] Stage seçimi runtime’da deterministic şekilde izlenir.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py -k "skips"`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — artifact stage and CLI parsing

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — submission stage arg + optional submission branch
- `mania_pipeline/tests/test_run_pipeline_s07_submission_contract.py` — skip flow assertion
