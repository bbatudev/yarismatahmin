# M001: Canonical Foundation — Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

## Project Description

Bu milestone, Kuzey Yıldızı’nın çekirdeğini kurar: tek komutla çalışan, tek gerçeklik üreten, leakage-safe ve tekrar üretilebilir canonical eğitim/eval hattı. Amaç model çeşitlendirmesi değil; notebook-script sapmasını teknik olarak kapatıp, Men/Women için güvenilir baseline ve run contract oluşturmaktır.

## Why This Milestone

Kullanıcının ana riski “yanlış iyileşme illüzyonu”dur (val/test karışması, farklı split/feature gerçeklikleri, tekrar edilemeyen skorlar). Bu milestone önce bunu çözer. Foundation oturmadan tuning/ensemble çalışmaları güvenilmez olur.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Tek canonical komutla feature→train→eval→report→artifact run alabilir.
- Men/Women için aynı standarda bağlı metrik + kalibrasyon + governance + regression gate çıktısını tek yerde görebilir.

### Entry point / environment

- Entry point: Python CLI (canonical run komutu)
- Environment: local dev
- Live dependencies involved: local filesystem, git metadata, Kaggle submission format (opsiyonel çıktı doğrulaması)

## Completion Class

- Contract complete means: split/leakage, execution-path, artifact, reproducibility ve regression gate kontratlarının mekanik olarak doğrulanması.
- Integration complete means: canonical komutun gerçek veride uçtan uca çalışıp tüm zorunlu çıktıları üretmesi.
- Operational complete means: aynı commit+seed koşusunda tolerans içi tekrar üretilebilirlik ve run-to-run delta kararının otomatik verilmesi.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Aynı komutla Men/Women run üretimi, metrik tabloları (Train/Val/Test 2024-2025) ve side-by-side özet satırı oluşuyor.
- Calibration bins CSV + ECE/W-MAE + overconfidence/drift özeti oluşuyor.
- Governance çıktısı keep/drop/candidate + `default_action` alanıyla ve ablation delta etkisiyle oluşuyor.
- Regression gate çoklu kuralı uygulanıyor: Brier zorunlu, calibration kötüleşirse fail, AUC bilgi amaçlı.
- Notebook ve script farklı eğitim yolu üretmiyor (single execution path enforcement).

## Risks and Unknowns

- Turnuva dağılım kayması — regular season sinyali turnuvada zayıflarsa baseline kararları yanıltabilir.
- Men/Women kalibrasyon davranış ayrışması — tek kalibrasyon yaklaşımı bir tarafta kötüleşme üretebilir.
- Mevcut notebook-script farkları — “iki farklı doğru” üretip karar kalitesini bozabilir.

## Existing Codebase / Prior Art

- `mania_pipeline/scripts/02_feature_engineering.py` — leakage hassas feature üretimi, split alanı ve Men/Women farkları.
- `mania_pipeline/scripts/03_lgbm_train.py` — baseline LightGBM eğitimi ve temel metrik raporu.
- `mania_pipeline/scripts/03_model_training.ipynb` — mevcut alternatif eğitim/eval akışı; parity/single-path açısından kritik.
- `csv dosyaları analiz/progress.md` — proje tarihçesi, riskler, karar geçmişi ve bekleyen işler.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001 — Canonical run komutu
- R002 — Deterministic walk-forward split
- R003 — Script/notebook parity
- R004 — Leakage guardrails
- R005 — Separate Men/Women tracks
- R006 — Standard metrics + side-by-side summary
- R007 — Calibration + overconfidence/drift report
- R008 — Feature governance ledger
- R009 — Controlled ablation reporting
- R010 — Artifact contract
- R011 — Reproducibility tolerance gate
- R012 — Optional submission validation
- R018 — Run regression gate
- R019 — Single execution path enforcement

## Scope

### In Scope

- Canonical execution pipeline ve tek giriş noktası
- Split/leakage kontrat doğrulamaları
- Men/Women standardize metrik-kalibrasyon-governance raporlama
- Artifact ve metadata standardizasyonu
- Reproducibility + regression gate

### Out of Scope / Non-Goals

- Hiperparametre araması (Optuna)
- Ensemble/stacking stratejileri
- Harici tracker (MLflow/W&B), DB, scheduler

## Technical Constraints

- No leakage: maç sonrası bilgi feature olamaz.
- Walk-forward sabit: Train<=2022, Val=2023, Test=2024-2025.
- Men/Women ayrı model dosyaları ve ayrı değerlendirme.
- Reproducibility toleransı: aynı commit+seed için |ΔBrier| <= 1e-4.

## Integration Points

- Local artifacts (`mania_pipeline/artifacts/...`) — model, rapor, metadata yazımı.
- Git repository state — commit hash ve run metadata izleme.
- Kaggle submission format — `ID,Pred` schema doğrulaması (opsiyonel).

## Open Questions

- Calibration default stratejisi isotonic mi platt mı başlamalı? — M001’de benchmark ile karar verilecek.
- Regression gate threshold’ları yalnız Brier için mi sabitlenecek? — Calibration fail koşulu ile birlikte finalize edilecek.
