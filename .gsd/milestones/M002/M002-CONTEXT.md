# M002: Probability Quality & Governance — Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

## Project Description

Bu milestone, M001’de kurulan canonical foundation üstüne olasılık kalitesini sistematik olarak iyileştirir. Odak, turnuva dağılım kayması ve Men/Women kalibrasyon ayrışmasını ölçülebilir politikalarla yönetmektir.

## Why This Milestone

M001 güvenilir ölçüm zemini sağlar; M002 bu zemin üzerinde kalite artışı sağlar. Buradaki amaç “daha karmaşık model” değil, karar kalitesi: hangi feature kalmalı, hangisi çıkmalı, kalibrasyon ne zaman hangi yöntemle uygulanmalı.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Feature governance kararlarını (keep/drop/candidate) run’dan bağımsız değil, delta ve ablation kanıtıyla verebilir.
- Men/Women ve sezon rejimi bazında kalibrasyon politikasını kontrollü şekilde seçebilir.

### Entry point / environment

- Entry point: canonical CLI run + governance/calibration policy komutları
- Environment: local dev
- Live dependencies involved: local artifacts and reports

## Completion Class

- Contract complete means: governance ve calibration policy kuralları deterministik ve raporlanabilir.
- Integration complete means: policy kararları canonical run ve regression gate ile uyumlu çalışır.
- Operational complete means: kötüleşme durumunda fallback/guardrail davranışı açık ve izlenebilir.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Kalibrasyon yöntemi seçimi (isotonic/platt) belirli veri rejimi koşullarına bağlanmış.
- Governance ledger kararları ablation deliliyle desteklenmiş.
- Turnuva dağılım kayması sinyalleri raporda görünür ve kararları etkiliyor.

## Risks and Unknowns

- Policy karmaşıklığı artıp okunabilirliği düşürebilir.
- Aşırı ablation döngüleri research hızını düşürebilir.
- Men/Women için farklı optimumlar bakım yükünü artırabilir.

## Existing Codebase / Prior Art

- `mania_pipeline/scripts/03_lgbm_train.py` — mevcut baseline eğitimi
- `mania_pipeline/scripts/analyze_weak_features.py` — governance başlangıç materyali
- `.gsd/REQUIREMENTS.md` — R009, R014, R018 ile ilgili kontratlar

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R007 — Calibration + overconfidence/drift
- R008 — Governance ledger
- R009 — Controlled ablation
- R014 — Advanced calibration policy by regime (deferred→active geçiş adayı)
- R018 — Regression gate politikasının güçlendirilmesi

## Scope

### In Scope

- Kalibrasyon policy kuralları
- Governance karar mekanizmasının sertleşmesi
- Dağılım kayması odaklı raporlama

### Out of Scope / Non-Goals

- Büyük mimari refactor
- Harici MLOps platform entegrasyonları

## Technical Constraints

- M001 canonical contract bozulamaz.
- Yeni policy adımları deterministic olmalı.
- Rapor formatı regression gate ile uyumlu kalmalı.

## Integration Points

- M001 artifact setleri — karşılaştırmalı analiz kaynağı
- Governance ledger — run-to-run karar hafızası

## Open Questions

- Drift alarm eşikleri sabit mi dinamik mi olmalı? — M002 planlama sırasında netleşecek.
- Kalibrasyon policy tek-pass mı iki-aşamalı mı olmalı? — maliyet/doğruluk dengesi değerlendirilecek.
