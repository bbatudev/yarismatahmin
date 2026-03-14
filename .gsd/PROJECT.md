# Project

## What This Is

Kuzey Yıldızı, NCAA March Machine Learning Mania 2026 için tek seferlik skor scripti değil, uzun ömürlü bir olasılık araştırma motorudur. Amaç, regular season gücü + turnuva bağlamı ile Men/Women için kalibre kazanma olasılıkları üretmek, leakage’i sıfırda tutmak ve Brier Score’u güvenilir şekilde iyileştirmektir.

## Core Value

Tek komutla çalışan, tek gerçeklik üreten, tekrar üretilebilir ve kararları geri izlenebilir bir olasılık pipeline’ı.

## Current State

S01 tamamlandı: canonical orchestrator artık mevcut (`mania_pipeline/scripts/run_pipeline.py`) ve tek komutla `feature -> train -> eval_report -> artifact` zincirini run-scoped metadata/lifecycle event contract’ı ile çalıştırıyor. Run artifact yüzeyi (`mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`, `stage_events.jsonl`, `eval_report.json`, `artifact_manifest.json`) stabilize edildi. Split/leakage gate, single execution path enforcement, calibration/governance ve reproducibility/regression gate katmanları hâlâ sonraki sliceların işi.

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
