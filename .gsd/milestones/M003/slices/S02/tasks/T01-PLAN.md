---
estimated_steps: 6
estimated_files: 2
---

# T01: Deterministic HPO trial engine

**Slice:** S02 — Reproducible HPO Search Harness
**Milestone:** M003

## Description

Train stage için deterministic trial param üretimi ve param override destekli train invocation katmanını ekler.

## Steps

1. HPO param search space sabitlerini tanımla.
2. Seed tabanlı deterministic trial generator yaz.
3. Param override + profile geçişi için train invocation wrapper ekle.
4. Per-gender trial loop ve candidate result toplama ekle.
5. Best trial seçimi (Val Brier) uygula.
6. Test ile deterministiklik kontratını doğrula.

## Must-Haves

- [ ] Aynı seed aynı trial param dizisini üretir.
- [ ] Train invocation eski imza ile de uyumlu kalır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_m003_s02_hpo_contract.py -k "reproducible" -q`

## Inputs

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/scripts/03_lgbm_train.py`

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/scripts/03_lgbm_train.py`
