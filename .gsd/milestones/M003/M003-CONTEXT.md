# M003: Submission-Ready Engine — Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

## Project Description

Bu milestone, canonical araştırma motorunu yarışma teslimine hazır karar motoruna çevirir: güvenilir inference, submission üretimi, release disiplini ve final kabul testleri.

## Why This Milestone

M001+M002 sonrası model kalitesi ve karar disiplini oturur; M003 bu birikimi operasyonel teslim sürecine bağlar. Amaç sadece CSV yazmak değil, güvenli ve izlenebilir teslim zinciri kurmaktır.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Tek komutla inference + submission üretip format ve içerik doğrulamasını geçebilir.
- “Bu submission hangi model/run’dan geldi?” sorusunu metadata ve artifact zinciriyle anında yanıtlayabilir.

### Entry point / environment

- Entry point: submission build komutu
- Environment: local dev + Kaggle upload-ready artifact
- Live dependencies involved: local artifacts, Kaggle format contract

## Completion Class

- Contract complete means: submission şeması, değer aralığı, kayıt bütünlüğü doğrulanmış.
- Integration complete means: eğitim artifact’ı → inference → submission zinciri kopuksuz.
- Operational complete means: release öncesi gate’ler ve raporlar otomatik üretiliyor.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Submission dosyası `ID,Pred` format doğrulamasından geçiyor.
- Pred değerleri [0,1] aralığında ve mapping kuralları deterministic.
- Submission ile ilişkili run/artifact metadata’sı eksiksiz.

## Risks and Unknowns

- Yanlış model artifact’ı ile submission üretimi
- Format doğru olsa da mapping hatası (ID eşleşme problemi)
- Son dakika değişikliklerinde regression gate bypass riski

## Existing Codebase / Prior Art

- `mania_pipeline/artifacts/data/*` — feature ve giriş verileri
- M001-M002’de üretilecek canonical model/artifact contract
- Kaggle yarışma submission formatı (`ID,Pred`)

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R010 — Artifact contract
- R012 — Optional submission generation and validation
- R015 — Ensemble layer (deferred, gerekirse)
- R018 — Regression gate continuity

## Scope

### In Scope

- Submission üretim hattı
- Submission doğrulama ve release check’leri
- Inference-çıktı izlenebilirliği

### Out of Scope / Non-Goals

- Harici workflow orchestrator
- Bulut-native serving altyapısı

## Technical Constraints

- M001/M002 karar kontratları korunacak.
- Submission mapping deterministic olacak.
- Release öncesi gate adımları atlanamayacak.

## Integration Points

- Canonical model artifacts
- Kaggle submission CSV contract

## Open Questions

- Ensemble bu milestone’da zorunlu mu opsiyonel mi kalmalı? — performans durumuna göre karar verilecek.
- Submission öncesi hangi minimum kalite eşiği zorunlu olacak? — M003 planlama aşamasında netleşecek.
