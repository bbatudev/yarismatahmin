# M003: Model Quality Expansion & Submission Readiness

**Vision:** M001+M002’de kurulan güvenilirlik/gate altyapısını bozmadan model kalite tavanını yükseltmek (HPO/ensemble), ardından submission-release hattını kalite eşiğiyle birlikte operasyonel hale getirmek.

## Success Criteria

- Canonical train stage, profile bazlı (baseline vs quality profile) deterministik eğitim kontratı üretir.
- HPO çıktıları machine-readable raporla (`hpo_report.json`) aday parametreleri ve kazanan profili kaydeder.
- Ensemble katmanı aktifse tekil model baseline’a karşı karşılaştırmalı kalite raporu üretir.
- Submission release yalnızca kalite eşiği + gate koşulları sağlandığında "ready" statüsü verir.

## Key Risks / Unknowns

- HPO kazanımı küçük kalabilir; gereksiz komplekslik riski.
- Ensemble, Women/Men için asimetrik fayda üretebilir.
- Kalite eşiği çok agresif tanımlanırsa release pipeline sürekli bloklanabilir.

## Proof Strategy

- Profile contract riski → retire in S01 by proving canonical train profile wiring and deterministic outputs.
- HPO riski → retire in S02 by proving reproducible search report and candidate ranking.
- Ensemble riski → retire in S03 by proving side-by-side baseline vs ensemble quality report.
- Release-gate riski → retire in S04 by proving policy-gated submission readiness artifact.

## Verification Classes

- Contract verification: training profile payload tests, HPO report schema tests, release readiness report tests.
- Integration verification: canonical run wiring (`feature->train->eval_report->artifact`) with profile/HPO/ready outputs.
- Operational verification: smoke runs + gate behavior under pass/fail readiness conditions.
- UAT / human verification: none

## Milestone Definition of Done

This milestone is complete only when all are true:

- S01-S04 slice deliverable’ları tamamlandı.
- Model quality artırımı en az bir canonical profile/hpo artefaktıyla kanıtlandı.
- Submission readiness kararı kalite eşiği + gate sinyalleriyle machine-readable raporda üretiliyor.
- Success criteria testler + canlı smoke run artefaktlarıyla doğrulandı.

## Requirement Coverage

- Covers: R013
- Partially covers: R015
- Supports continuity: R012, R018
- Orphan risks: none

## Slices

- [x] **S01: Training Profile Contract (Baseline vs Quality v1)** `risk:high` `depends:[]`
  > After this: canonical train stage profile seçimini (`baseline|quality_v1`) payload + metadata’da deterministik üretir.

- [x] **S02: Reproducible HPO Search Harness** `risk:high` `depends:[S01]`
  > After this: HPO adayları ve kazanan konfigürasyon `hpo_report.json` ile izlenebilir olur.

- [ ] **S03: Ensemble Candidate Integration** `risk:medium` `depends:[S02]`
  > After this: baseline vs ensemble kalite karşılaştırması ve seçim sinyali canonical eval yüzeyine bağlanır.

- [ ] **S04: Submission Readiness Final Gate** `risk:medium` `depends:[S03]`
  > After this: quality-threshold + policy gate + submission contract birleşik readiness raporu üretilir.

## Boundary Map

### S01 → S02

Produces:
- `stage_outputs.train.training_profile`
- `train_profile_report.json` (opsiyonel detay)

Consumes:
- Existing canonical feature/train payload contracts

### S02 → S03

Produces:
- `hpo_report.json`
- `stage_outputs.train.hpo`

Consumes:
- S01 training profile outputs

### S03 → S04

Produces:
- `ensemble_report.json`
- `stage_outputs.eval_report.ensemble`

Consumes:
- S02 HPO outputs + baseline train artifacts

### Final integration (S04)

Produces:
- `submission_readiness_report.json`
- end-to-end acceptance artifact (quality + gate + submission contract)

Consumes:
- S01-S03 outputs in canonical run payloads
