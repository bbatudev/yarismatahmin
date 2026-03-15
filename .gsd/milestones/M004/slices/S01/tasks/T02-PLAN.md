---
estimated_steps: 4
estimated_files: 2
---

# T02: Comparison harness script + test

**Slice:** S01 — Benchmark Lock + Evaluation Harness
**Milestone:** M004

## Description

İki run_metadata arasında metrik delta hesaplayan script ve testini ekle.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_compare_run_metrics.py -q`
