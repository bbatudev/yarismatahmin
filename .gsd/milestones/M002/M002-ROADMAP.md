# M002: Probability Quality & Governance

**Vision:** M001’de güvence altına alınan canonical run kontratlarını bozmadan, kalibrasyon kararlarını rejim-bazlı hale getirmek ve drift sinyallerini governance karar mekanizmasına bağlayarak olasılık kalitesini operasyonel olarak iyileştirmek.

## Success Criteria

- Canonical run rejim-bazlı drift raporu üretir ve Men/Women için karar-eşik sinyalleri machine-readable görünür olur.
- Kalibrasyon yöntemi seçimi (none/isotonic/platt) rejim kuralına bağlı deterministik policy çıktısı üretir.
- Governance kararları sadece importance/açık ablation değil, drift+kalibrasyon etkisiyle birlikte gerekçelendirilir.
- Regression gate, policy katmanından gelen yeni kalite sinyallerini consume ederek fallback/guardrail davranışını açıkça raporlar.

## Key Risks / Unknowns

- Rejim tanımı (ör. seed spread, split, probability band) yanlış kalibre edilirse policy gürültü üretir.
- Kalibrasyon method seçimi düşük örnekli splitlerde overfit/yanıltıcı iyileşme üretebilir.
- Drift sinyallerinin governance kararına agresif bağlanması gereksiz feature drop riskini artırabilir.

## Proof Strategy

- Rejim tanımı belirsizliği → retire in S01 by proving canonical drift/regime report produces stable, interpretable signals on smoke runs.
- Kalibrasyon policy riski → retire in S02 by proving deterministic method-selection contract and comparable before/after deltas.
- Governance aşırı tepkisellik riski → retire in S03 by proving decision fusion uses multi-evidence with reason-coded confidence.

## Verification Classes

- Contract verification: policy selector tests, drift report schema tests, governance decision payload tests.
- Integration verification: canonical run ile eval+artifact payload’larında policy/drift/governance wiring doğrulaması.
- Operational verification: regression gate’in policy sinyalleriyle pass/fail/fallback davranışı.
- UAT / human verification: none

## Milestone Definition of Done

This milestone is complete only when all are true:

- S01-S04 slice deliverable’ları tamamlandı.
- Drift/policy/governance yüzeyleri canonical run içinde birlikte bağlı çalışıyor.
- Tek canonical entrypoint gerçek run’da policy+gate kararını üretiyor.
- Success criteria canlı run artifact’ları ve testlerle yeniden doğrulandı.
- Final integration senaryosu (policy-enabled smoke + gate behavior) pass verdi.

## Requirement Coverage

- Covers: R014
- Partially covers: R018
- Leaves for later: R013, R015
- Orphan risks: none

## Slices

- [x] **S01: Regime Drift Baseline & Signal Contract** `risk:high` `depends:[]`
  > After this: Canonical run `drift_regime_report.json` üretir ve Men/Women için rejim sinyalleri eval/artifact payload’ına bağlanır.

- [ ] **S02: Regime-Aware Calibration Policy Engine** `risk:high` `depends:[S01]`
  > After this: Kalibrasyon method seçimi policy kontratıyla deterministik yürür ve before/after kalite deltasını raporlar.

- [ ] **S03: Governance Decision Fusion (Ablation + Drift + Calibration)** `risk:medium` `depends:[S01,S02]`
  > After this: Governance decision surface reason-coded confidence ile multi-evidence karar üretir.

- [ ] **S04: Policy-Gated Final Integration** `risk:medium` `depends:[S03]`
  > After this: Regression gate policy sinyallerini consume eder ve milestone final integration proof’u canonical run’da alınır.

## Boundary Map

### S01 → S02

Produces:
- `drift_regime_report.json` artifact schema (`gender`, `regime`, `metrics`, `alert_flags`)
- `stage_outputs.eval_report.drift` payload

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- `calibration_policy_report.json` (`selected_method`, `candidate_metrics`, `reason`, `fallback`)
- `stage_outputs.eval_report.calibration_policy`

Consumes:
- S01 drift regime signal payload

### S03 → S04

Produces:
- `governance_decision_report.json` (`decision`, `confidence`, `evidence_bundle`, `reason_codes`)
- `stage_outputs.eval_report.governance_decision`

Consumes:
- S02 calibration policy outputs
- Existing S05 governance+ablation outputs

### Final integration (S04)

Produces:
- policy-enabled regression gate behavior report
- end-to-end milestone acceptance artifact tying drift/policy/governance/gate decisions

Consumes:
- S01-S03 outputs in canonical run payloads
