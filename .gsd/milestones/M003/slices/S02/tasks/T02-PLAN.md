---
estimated_steps: 5
estimated_files: 2
---

# T02: HPO report and CLI wiring

**Slice:** S02 — Reproducible HPO Search Harness
**Milestone:** M003

## Description

HPO ayarlarını CLI/context’ten alır, train payload’a `hpo` bloğunu yazar ve `hpo_report.json` artifact’ını persist eder.

## Steps

1. CLI args (`--hpo-trials`, `--hpo-target-profile`) ekle.
2. Main context’e HPO config alanlarını yaz.
3. Stage_train dönüşüne `hpo` payload ekle.
4. `hpo_report.json` dosyasını yaz.
5. Contract testlerini çalıştır.

## Must-Haves

- [ ] HPO kapalıyken (`trials=0`) status=skipped raporu yine yazılır.
- [ ] HPO açıkken best trial alanları payload’da görünür.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py`

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py`
