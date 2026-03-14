# M001: Canonical Foundation

**Vision:** NCAA turnuva olasılık tahmininde tek gerçeklik üreten, leakage-safe, tekrar üretilebilir ve kararları geri izlenebilir canonical pipeline kurmak.

## Success Criteria

- Tek canonical komut gerçek veride feature → train → eval → calibration → governance → artifact akışını uçtan uca çalıştırır.
- Men/Women için Train/Val/Test(2024-2025) metrikleri ve side-by-side özet satırı otomatik üretilir.
- Calibration bins CSV + ECE/W-MAE + overconfidence/drift özeti üretilir.
- Governance raporu keep/drop/candidate + `default_action` + ablation delta etkisini içerir.
- Reproducibility ve regression gate (Brier zorunlu, calibration kötüleşmesi fail, AUC bilgi) otomatik pass/fail üretir.
- Notebook ve script farklı eğitim yolu üretemez (single execution path enforcement).

## Key Risks / Unknowns

- Turnuva dağılım kayması — regular season sinyalinin playoff’ta zayıflaması yanlış feature kararına yol açabilir.
- Notebook-script sapması — paralel eğitim yolları farklı “doğru” üretebilir.
- Kalibrasyon ayrışması — Men/Women’da aynı yöntem zıt etki gösterebilir.

## Proof Strategy

- Turnuva dağılım kayması görünürlüğü → retire in S04/S05 by proving calibration+ablation delta raporlarının run kararına bağlandığı.
- Notebook-script sapması → retire in S03 by proving eğitim tek execution path üzerinden koşuyor.
- Kalibrasyon ayrışması → retire in S04 by proving Men/Women ayrı calibration çıktısı ve drift özeti üretiliyor.

## Verification Classes

- Contract verification: split/leakage checker, artifact schema checker, submission format checker, regression gate kuralları.
- Integration verification: canonical komutun gerçek CSV verisiyle uçtan uca çalıştırılması.
- Operational verification: aynı commit+seed için reproducibility toleransı (|ΔBrier| <= 1e-4) doğrulaması.
- UAT / human verification: rapor okunabilirliği ve governance kararlarının anlamlılığı.

## Milestone Definition of Done

This milestone is complete only when all are true:

- Tüm slice deliverable’ları tamamlandı.
- Ortak bileşenler gerçek pipeline içinde bağlı çalışıyor.
- Tek canonical entrypoint var ve gerçek run ile çalıştırıldı.
- Başarı kriterleri artifact ve canlı komut çıktılarıyla yeniden doğrulandı.
- Final entegrasyon senaryosu (optional submission dahil) pass verdi.

## Requirement Coverage

- Covers: R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R011, R012, R018, R019
- Partially covers: none
- Leaves for later: R013, R014, R015
- Orphan risks: none

## Slices

- [x] **S01: Canonical Run Orchestrator** `risk:medium` `depends:[]`
  > After this: Tek komutla feature→train→eval→report→artifact zinciri tetiklenir.

- [x] **S02: Split/Leakage Contract Gates** `risk:high` `depends:[S01]`
  > After this: Walk-forward split ve leakage kuralları ihlal edildiğinde run fail verir.

- [x] **S03: Unified Men/Women Eval Core + Single Execution Path Enforcement** `risk:high` `depends:[S02]`
  > After this: Men/Women metrik tablosu + side-by-side özet üretilir ve eğitim yolu script-first tek gerçeklikte kilitlenir.

- [x] **S04: Calibration Layer + Overconfidence/Drift Reporting** `risk:high` `depends:[S03]`
  > After this: calibration bins + ECE/W-MAE + üst olasılık bin sapma özeti çıkar.

- [x] **S05: Feature Governance + Controlled Ablation** `risk:medium` `depends:[S03]`
  > After this: keep/drop/candidate + `default_action` ve ablation delta raporu otomatik oluşur.

- [x] **S06: Artifact Contract + Reproducibility + Regression Gate** `risk:high` `depends:[S04,S05]`
  > After this: run metadata, reproducibility toleransı ve çoklu-kural regression pass/fail kararı üretilir.

- [ ] **S07: Optional Submission Validation + Final Integration** `risk:medium` `depends:[S06]`
  > After this: Submission `ID,Pred` doğrulamasıyla birlikte tüm canonical hattın final entegrasyon kanıtı alınır.

## Boundary Map

### S01 → S02

Produces:
- `run_pipeline` CLI entrypoint (tek komut tetikleyici)
- Standard run context object (`run_id`, `seed`, `git_commit`, timestamps)
- Stage lifecycle log contract (feature/train/eval/report/artifact)

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- Deterministic split validator (Train<=2022, Val=2023, Test=2024-2025)
- Leakage checker (post-game bilgi kullanımı ve split ihlal alarmı)
- Gate result schema (`pass/fail`, `reason`, `blocking_rule`)

Consumes from S01:
- Stage lifecycle hooks
- Run context object

### S03 → S04

Produces:
- Men/Women unified training-eval core
- Metrics table schema (Brier, LogLoss, AUC by Train/Val/Test)
- Men-vs-Women side-by-side summary row
- Single execution path enforcement (script eğitim tek kaynak, notebook eğitim kapalı)

Consumes from S02:
- Split/leakage gate pass state

### S03 → S05

Produces:
- Standard model outputs/probabilities for governance analysis
- Feature namespace contract (final feature list snapshot per run)

Consumes from S02:
- Split/leakage gate pass state

### S04 → S06

Produces:
- Calibration bins CSV contract
- Calibration summary metrics (ECE/W-MAE)
- Overconfidence/drift summary contract (high-prob bin realized gap)

Consumes from S03:
- Men/Women probability outputs

### S05 → S06

Produces:
- Governance ledger schema (`feature`, `group`, `default_action`, `evidence`)
- Ablation delta schema (ΔBrier, ΔLogLoss, ΔAUC, ΔCalibration)

Consumes from S03:
- Feature list snapshot
- Baseline evaluation outputs

### S06 → S07

Produces:
- Artifact bundle contract (model, feature list, run metadata, reports)
- Reproducibility check result (|ΔBrier| <= 1e-4)
- Regression gate result (Brier required, calibration degradation fail, AUC informational)

Consumes from S04/S05:
- Calibration outputs
- Governance/ablation outputs

### Final integration (S07)

Produces:
- Submission builder output (`ID,Pred`)
- Submission validator report (schema/range/null checks)
- End-to-end acceptance report tying gates + artifacts + submission readiness

Consumes from S06:
- Approved canonical artifacts and gate outcomes
