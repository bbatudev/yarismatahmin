# M001/S07 — Research

**Date:** 2026-03-15

## Summary

S07’nin kalan tek requirement’ı R012: optional submission generation + schema doğrulaması. S06’da artifact stage policy gate modeli hazır olduğu için submission üretimi de aynı katmanda emit edilirse lifecycle/topology bozulmadan final integration kapanabiliyor.

Mevcut kod tabanında inference için 2026 matchup feature builder yok; bu slice’ın hedefi submission kalitesinden çok operatif güvenlik: `ID,Pred` formatının deterministic üretilmesi ve strict doğrulanması. Bu nedenle `--submission-stage {none,stage1,stage2}` ile Kaggle sample ID yüzeyini kullanıp valid submission dosyası üretmek en düşük-risk yaklaşım.

## Recommendation

`stage_artifact` içine optional submission branch’i ekle:
- `submission_stage=none` => skip + reason-coded report
- `submission_stage=stage1|stage2` => ilgili sample dosyasından `ID` al, `Pred` üret, schema/range/null validation yap, fail-fast enforce et.

Outputlar:
- `submission_<stage>.csv`
- `submission_validation_report.json`
- `stage_outputs.artifact.submission` + `artifact_manifest.json.contracts.submission`

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Submission ID kaynağı | Kaggle sample submission dosyaları (`SampleSubmissionStage1/2.csv`) | Format canonical ve yarışma şemasına birebir uyumlu |
| Gate/result observability | S06 report-first + fail-fast artifact pattern | S07’de de aynı diagnostic ergonomiyi korur |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py::stage_artifact` — contract/gate raporlarının tek toplandığı yer.
- `mania_pipeline/tests/test_run_pipeline_s06_artifact_repro_regression_contract.py` — artifact-stage policy test pattern’i.
- `march-machine-leraning-mania-2026/SampleSubmissionStage1.csv`, `SampleSubmissionStage2.csv` — authoritative submission ID sources.

## Constraints

- Stage topology değişmemeli.
- Submission üretimi opsiyonel olmalı (default davranış değişmemeli).
- Validation failure stage-level fail vermeli.

## Common Pitfalls

- **Kolon ad/sıra sapması** — tam `ID,Pred` sırası dışında dosya geçerli sayılmamalı.
- **Range kontrolünü atlamak** — `Pred` için `[0,1]` aralığı zorunlu.

## Open Risks

- Pred değerleri şu aşamada placeholder üretildiği için kalite sinyali yok; bu intentional ve R012 kapsamı içinde.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Pipeline contract hardening | debug-like-expert | available |

## Sources

- R012 sahiplik/amaç (source: [`.gsd/REQUIREMENTS.md`](../../../../REQUIREMENTS.md)).
- S06 artifact contract pattern (source: [`.gsd/milestones/M001/slices/S06/S06-SUMMARY.md`](../S06/S06-SUMMARY.md)).
- Sample submission kaynak dosyaları (source: [`march-machine-leraning-mania-2026/SampleSubmissionStage1.csv`](../../../../../march-machine-leraning-mania-2026/SampleSubmissionStage1.csv), [`march-machine-leraning-mania-2026/SampleSubmissionStage2.csv`](../../../../../march-machine-leraning-mania-2026/SampleSubmissionStage2.csv)).
