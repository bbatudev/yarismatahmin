# Requirements

This file is the explicit capability and coverage contract for the project.

Use it to track what is actively in scope, what has been validated by completed work, what is intentionally deferred, and what is explicitly out of scope.

Guidelines:
- Keep requirements capability-oriented, not a giant feature wishlist.
- Requirements are atomic, testable, and written in plain language.
- Every active requirement is mapped to an owner slice or milestone.
- Research-informed items stay advisory unless confirmed.

## Active

## Validated

### R001 — Canonical end-to-end run command
- Class: primary-user-loop
- Status: validated
- Description: Tek komut feature → train → eval → report → artifact akışını uçtan uca çalıştırır.
- Why it matters: Dağınık adımları ve insan kaynaklı hata riskini kaldırır.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S06, M001/S07
- Validation: validated by execution
- Notes: `mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke` gerçek veriyle koştu; run metadata + stage lifecycle contract doğrulandı.

### R002 — Deterministic walk-forward split standard
- Class: quality-attribute
- Status: validated
- Description: Train<=2022, Val=2023, Test=2024-2025 standardı tüm run’larda zorunlu uygulanır.
- Why it matters: Val/test karışması ve yanlış iyileşme illüzyonunu engeller.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S03
- Validation: validated by execution
- Notes: S02’de split gate runtime’a bağlandı; `test_split_leakage_contracts.py` + `test_run_pipeline_split_leakage_gate.py` + `s02_split_leakage_smoke` run metadata (`stage_outputs.feature.gates`) ile doğrulandı.

### R004 — Leakage guardrails and checks
- Class: compliance/security
- Status: validated
- Description: Maç sonrası bilgi sızıntısını otomatik kontrollerle fail eder.
- Why it matters: Offline skorların sahte iyileşmesini önler.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S07
- Validation: validated by execution
- Notes: S02’de leakage gate fail-fast enforce edildi; `feature` stage failed event error.message içinde `blocking_rule` doğrulandı ve pass durumda gate payload’ı metadata’ya persist edildi.

### R003 — Script/notebook parity contract
- Class: continuity
- Status: validated
- Description: Feature/split gerçekliği tek kaynaktan gelir; notebook farklı eğitim gerçekliği üretemez.
- Why it matters: İki farklı “doğru” olmasını önler.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S07
- Validation: validated by execution
- Notes: S03’te notebook reporting-only role’e indirildi; `test_notebook_execution_path_guard.py` forbidden training/persist primitive’lerini fail ediyor.

### R005 — Separate Men/Women model tracks
- Class: core-capability
- Status: validated
- Description: Men ve Women eğitim/eval akışları ayrı yürütülür ve ayrı artifact üretir.
- Why it matters: Cinsiyetler arası davranış farkını maskelemeyi önler.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S04
- Validation: validated by execution
- Notes: S03’te unified core ile ayrı gender payload/artifact kontratı (`stage_outputs.train.genders.{men,women}`) runtime’da doğrulandı.

### R006 — Standard metrics + side-by-side summary
- Class: failure-visibility
- Status: validated
- Description: Train/Val/Test için Brier, LogLoss, AUC raporlanır; ek olarak Men vs Women yan-yana özet satırı zorunludur.
- Why it matters: Performans ve cinsiyet farkı tek bakışta görülebilir.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S06
- Validation: validated by execution
- Notes: S03 canonical runtime’da `eval_report.json` içine `metrics_table` + `side_by_side_summary` kontratıyla doğrulandı.

### R007 — Calibration + overconfidence/drift report
- Class: quality-attribute
- Status: validated
- Description: Calibration bins CSV + ECE veya W-MAE + üst olasılık binlerinde gerçekleşme farkı (overconfidence/drift özeti) üretilir.
- Why it matters: Brier hedefi için olasılık güvenilirliğini görünür ve yönetilebilir yapar.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S06
- Validation: validated by execution
- Notes: S04 canonical run (`20260314T161222Z_s04_calibration_smoke`) ile `calibration_bins.csv` + `calibration_report.json` artifact’ları, `eval_report.json.calibration` wiring’i ve empty-band diagnostics sözleşmesi doğrulandı.

### R008 — Feature governance ledger
- Class: operability
- Status: validated
- Description: Her run sonunda feature’lar keep/drop/candidate olarak sınıflanır.
- Why it matters: Feature kararlarını geri izlenebilir ve tutarlı kılar.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M001/S06
- Validation: validated by execution
- Notes: S05 canonical run (`20260314T210035Z_s05_governance_smoke`) ile `governance_ledger.csv` artifact’ı ve `eval_report/run_metadata` governance wiring’i doğrulandı.

### R009 — Controlled ablation reporting
- Class: quality-attribute
- Status: validated
- Description: Şüpheli feature grupları için ablation etkisi (delta Brier/LogLoss/AUC/Calibration) standart raporlanır.
- Why it matters: Zayıf lineer korelasyonlu ama non-linear faydalı sinyallerin yanlış silinmesini engeller.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M002/S01 (provisional)
- Validation: validated by execution
- Notes: S05 canonical run’da `ablation_report.json`, `executed_group_count` ve reason-coded `skipped_groups` contract yüzeyleri runtime assertion’larla doğrulandı.

### R010 — Artifact contract
- Class: launchability
- Status: validated
- Description: Model dosyaları, kullanılan feature listesi, run metadata (git commit, komut, tarih, seed) zorunlu artifact seti olarak üretilir.
- Why it matters: Run tekrar üretimi ve audit mümkün olur.
- Source: user
- Primary owning slice: M001/S06
- Supporting slices: M001/S07
- Validation: validated by execution
- Notes: S06 ile `artifact_contract_report.json` required artifact var/yok kontratını üretip eksik durumda fail-fast enforce ediyor.

### R011 — Reproducibility tolerance gate
- Class: continuity
- Status: validated
- Description: Aynı commit + aynı seed koşusunda metrik farkı tolerans içinde kalmalıdır (örn. |ΔBrier| <= 1e-4).
- Why it matters: “Aynı kod farklı sonuç” problemini operasyonel olarak kilitler.
- Source: user
- Primary owning slice: M001/S06
- Supporting slices: none
- Validation: validated by execution
- Notes: S06 run’larında `reproducibility_report.json` same commit+seed baseline ile pass/skip/fail üretir; breach stage fail olur.

### R018 — Run regression gate
- Class: failure-visibility
- Status: validated
- Description: Her run önceki canonical run’a karşı delta raporu üretir ve pass/fail kararı verir.
- Why it matters: Sessiz kalite düşüşlerini engeller.
- Source: user
- Primary owning slice: M001/S06
- Supporting slices: M002/S01, M002/S03, M002/S04
- Validation: validated by execution
- Notes: S06 ile `regression_gate_report.json` Brier mandatory + calibration degradation fail + AUC informational policy’sini enforce eder; S03 karar evidence yüzeyini kurdu, S04 ise policy-conditioned fallback/warning davranışını `policy_gate_report.json` ile canonical artifact katmanına bağladı.

### R012 — Optional submission generation and validation
- Class: integration
- Status: validated
- Description: İsteğe bağlı submission tek komutla üretilir ve `ID,Pred` format doğrulamasından geçer.
- Why it matters: Araştırmadan yarışma teslimine geçişi güvenli hale getirir.
- Source: user
- Primary owning slice: M001/S07
- Supporting slices: M003/S04
- Validation: validated by execution
- Notes: S07’de `--submission-stage stage2` runtime proof’u ile `submission_stage2.csv` + strict validation report (`submission_validation_report.json`) kontratı doğrulandı; M003/S04’te bu sinyaller `submission_readiness_report.json` altında final readiness fusion kararına bağlandı.

### R019 — Single execution path enforcement
- Class: constraint
- Status: validated
- Description: Eğitim için iki ayrı yol bırakılmaz; script tek kaynak olur, notebook eğitim yürütmez.
- Why it matters: Notebook-script sapmasını teknik olarak kapatır.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S07
- Validation: validated by execution
- Notes: S03’te notebook authority guard testi ile eğitim/persist primitive geri gelişi CI seviyesinde fail ediliyor.

### R014 — Advanced calibration policy by regime
- Class: differentiator
- Status: validated
- Description: Men/Women ve sezon rejimine göre isotonic/platt/none seçim politikasının sistematikleştirilmesi.
- Why it matters: Kalibrasyon davranış ayrışmasını daha iyi yönetir.
- Source: inferred
- Primary owning slice: M002/S02
- Supporting slices: M002/S01, M002/S03
- Validation: validated by execution
- Notes: S02’de `calibration_policy_report.json` + `stage_outputs.eval_report.calibration_policy` contract’ı test-suite ve `m002_s02_policy_smoke` runtime proof ile doğrulandı.

### R013 — Hyperparameter optimization (Optuna)
- Class: quality-attribute
- Status: validated
- Description: Hiperparametre araması ile baseline üstü performans aranması.
- Why it matters: M003 model kalite tavanını yükseltir.
- Source: user
- Primary owning slice: M003/S02
- Supporting slices: M003/S01
- Validation: validated by execution
- Notes: S02’de deterministic HPO trial harness (`--hpo-trials`, `hpo_report.json`, `stage_outputs.train.hpo`) test-suite ve `m003_s02_hpo_smoke` runtime proof ile doğrulandı.

### R015 — Ensemble layer beyond baseline LGBM
- Class: core-capability
- Status: validated
- Description: Birden çok modelin weighted/stacked kombinasyonu.
- Why it matters: Tek model kırılganlığını azaltabilir.
- Source: inferred
- Primary owning slice: M003/S03
- Supporting slices: M003/S02
- Validation: validated by execution
- Notes: S03’te `ensemble_report.json` + `stage_outputs.eval_report.ensemble` contract’ı test-suite ve `m003_s03_ensemble_smoke` runtime proof ile doğrulandı.

## Deferred

## Out of Scope

### R016 — External experiment tracker integration
- Class: anti-feature
- Status: out-of-scope
- Description: MLflow/W&B gibi dış deney takip sistemlerinin entegrasyonu.
- Why it matters: Erken entegrasyon scope’u dağıtır.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Local+git+Kaggle sınırında kalınacak.

### R017 — Cloud scheduler / DB orchestration
- Class: anti-feature
- Status: out-of-scope
- Description: Bulut scheduler, DB-backed run orchestrasyonu, servisleşmiş MLOps katmanı.
- Why it matters: Mevcut hedef için gereksiz operasyonel yük.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: İleri fazlarda tekrar değerlendirilebilir.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | validated | M001/S01 | M001/S06,S07 | validated (S01 integration runtime + contract checks) |
| R002 | quality-attribute | validated | M001/S02 | M001/S03 | validated (S02 split gate contract + integration/runtime checks) |
| R003 | continuity | validated | M001/S03 | M001/S07 | validated (S03 notebook guard + script-first runtime evidence) |
| R004 | compliance/security | validated | M001/S02 | M001/S07 | validated (S02 leakage fail-fast + blocking_rule diagnostics + metadata persistence) |
| R005 | core-capability | validated | M001/S03 | M001/S04 | validated (S03 unified core + separate men/women artifacts) |
| R006 | failure-visibility | validated | M001/S03 | M001/S06 | validated (S03 metrics_table + side_by_side_summary runtime contract) |
| R007 | quality-attribute | validated | M001/S04 | M001/S06 | validated (S04 calibration contract tests + canonical smoke run artifacts and eval wiring checks) |
| R008 | operability | validated | M001/S05 | M001/S06 | validated (S05 governance ledger contract test + canonical smoke run metadata/eval wiring checks) |
| R009 | quality-attribute | validated | M001/S05 | M002/S01 | validated (S05 ablation delta contract tests + canonical smoke run artifact assertions) |
| R010 | launchability | validated | M001/S06 | M001/S07 | validated (S06 artifact contract report + required-file fail-fast checks in runtime and tests) |
| R011 | continuity | validated | M001/S06 | none | validated (S06 reproducibility report with same commit+seed tolerance pass/fail enforcement) |
| R012 | integration | validated | M001/S07 | M003/S04 | validated (S07 submission stage runtime proof + strict `ID,Pred` validation report checks + S04 readiness fusion report) |
| R014 | differentiator | validated | M002/S02 | M002/S01,S03 | validated (S02 policy report contract + canonical smoke proof) |
| R018 | failure-visibility | validated | M001/S06 | M002/S01,S03,S04 | validated (S06 regression gate report + S04 policy-gated fallback diagnostics) |
| R019 | constraint | validated | M001/S03 | M001/S07 | validated (S03 notebook authority guardrail test) |
| R013 | quality-attribute | validated | M003/S02 | M003/S01 | validated (S02 deterministic HPO report contract + canonical smoke proof) |
| R015 | core-capability | validated | M003/S03 | M003/S02 | validated (S03 ensemble report contract + canonical smoke proof) |
| R016 | anti-feature | out-of-scope | none | none | n/a |
| R017 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 0
- Mapped to slices: 0
- Validated: 17
- Unmapped active requirements: 0
