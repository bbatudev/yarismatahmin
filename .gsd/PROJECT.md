# Project

## What This Is

Kuzey Yıldızı, NCAA March Machine Learning Mania 2026 için tek seferlik skor scripti değil, uzun ömürlü bir olasılık araştırma motorudur. Amaç, regular season gücü + turnuva bağlamı ile Men/Women için kalibre kazanma olasılıkları üretmek, leakage’i sıfırda tutmak ve Brier Score’u güvenilir şekilde iyileştirmektir.

## Core Value

Tek komutla çalışan, tek gerçeklik üreten, tekrar üretilebilir ve kararları geri izlenebilir bir olasılık pipeline’ı.

## Current State

S01+S02+S03 tamamlandı: canonical orchestrator (`mania_pipeline/scripts/run_pipeline.py`) tek komutla `feature -> train -> eval_report -> artifact` zincirini çalıştırıyor, `feature` stage içinde split/leakage contract gate’lerini fail-fast enforce ediyor ve `train` stage artık gate-pass precondition olmadan başlamıyor. Men/Women eğitim/eval tek çekirdek kontratta birleşti: `run_metadata.json -> stage_outputs.train` altında per-gender model + `metrics_by_split` + `feature_snapshot` persist ediliyor; `eval_report.json` artık normalize `metrics_table` (Train/Val/Test × Brier/LogLoss/AUC) ve `side_by_side_summary` (Men vs Women Test delta) üretiyor. Notebook eğitim otoritesi teknik olarak kapatıldı (`03_model_training.ipynb` reporting-only + `test_notebook_execution_path_guard.py`). Kalan ana işler: S04 calibration/drift, S05 governance/ablation, S06 reproducibility+regression gates, S07 submission validation.

## Architecture / Key Patterns

- Python tabanlı data→feature→model hattı
- Men/Women ayrı modelleme yolu
- Walk-forward split (Train<=2022, Val=2023, Test=2024-2025)
- Artifact-first yaklaşım (model, feature list, run metadata)
- Kalibrasyon ve governance çıktılarının raporlanması
- Script-first canonical execution (notebook eğitim yolu olmadan, raporlama/inceleme aracı olarak)

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: Canonical Foundation — Tek execution path, leakage-safe eval, reproducible baseline ve run contract
- [ ] M002: Probability Quality & Governance — Kalibrasyon davranışı, dağılım kayması odaklı governance/ablation ve karar kalitesi
- [ ] M003: Submission-Ready Engine — E2E inference, submission operasyonu, release/readiness sertleşmesi
