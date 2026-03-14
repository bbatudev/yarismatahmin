# Project

## What This Is

Kuzey Yıldızı, NCAA March Machine Learning Mania 2026 için tek seferlik skor scripti değil, uzun ömürlü bir olasılık araştırma motorudur. Amaç, regular season gücü + turnuva bağlamı ile Men/Women için kalibre kazanma olasılıkları üretmek, leakage’i sıfırda tutmak ve Brier Score’u güvenilir şekilde iyileştirmektir.

## Core Value

Tek komutla çalışan, tek gerçeklik üreten, tekrar üretilebilir ve kararları geri izlenebilir bir olasılık pipeline’ı.

## Current State

S01+S02+S03+S04+S05+S06+S07 tamamlandı ve M001 kapandı: canonical orchestrator (`mania_pipeline/scripts/run_pipeline.py`) tek komutla `feature -> train -> eval_report -> artifact` zincirini çalıştırıyor, split/leakage gate’leri fail-fast enforce ediyor, train/eval kalibrasyon/governance kontratlarını machine-readable artifact’larla persist ediyor ve artifact stage’de contract/gate katmanı (`artifact_contract_report.json`, `reproducibility_report.json`, `regression_gate_report.json`) ile blocking breach durumlarını stage-level fail semantics ile yönetiyor. S07 ile optional submission branch’i (`--submission-stage stage1|stage2`) eklendi; `submission_<stage>.csv` + `submission_validation_report.json` strict `ID,Pred` schema/range/null doğrulamasıyla canonical run’a bağlandı. M002 tamamlandı: drift (`drift_regime_report.json`), calibration policy (`calibration_policy_report.json`), governance decision (`governance_decision_report.json`) ve policy-gate integration (`policy_gate_report.json`) yüzeyleri canonical akışa eklendi; S04 ile regression gate policy-conditioned fallback/warning davranışı machine-readable hale geldi. M003/S01 tamamlandı: train stage profile-aware oldu (`--training-profile baseline|quality_v1`) ve profile metadata’sı `stage_outputs.train` altında persist edilmeye başladı. Notebook eğitim otoritesi teknik olarak kapalı (`03_model_training.ipynb` reporting-only + guard tests). Sonraki ana iş M003/S02: reproducible HPO harness.

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

- [x] M001: Canonical Foundation — Tek execution path, leakage-safe eval, reproducible baseline ve run contract
- [x] M002: Probability Quality & Governance — Kalibrasyon davranışı, dağılım kayması odaklı governance/ablation ve karar kalitesi
- [ ] M003: Submission-Ready Engine — E2E inference, submission operasyonu, release/readiness sertleşmesi
