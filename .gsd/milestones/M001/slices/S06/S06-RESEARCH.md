# M001/S06 — Research

**Date:** 2026-03-15

## Summary

S06 scope R010/R011/R018 için mevcut en güvenli seam `stage_artifact`. S01’den beri run metadata ve stage event yüzeyi sabit, S04/S05 ise eval katmanında calibration+governance artifact’larını zaten machine-readable üretiyor. Bu yüzden artifact-contract doğrulaması, reproducibility kontrolü ve regression gate kararını yeni stage açmadan `artifact` içinde toplamak topology riskini en düşükte tutuyor.

Risk noktası, gate kararını sadece tek bir metriğe yaslamak: D005 buna zaten karşı. Bu slice’da Brier’i zorunlu ve bloklayıcı, calibration bozulmasını bloklayıcı, AUC’yi bilgi amaçlı tuttuk. Reproducibility ise ayrı bir kontrat olarak “aynı commit+seed, |ΔBrier|<=1e-4” kuralıyla çalışmalı ve breach durumunda run fail vermeli.

## Recommendation

`run_pipeline.py::stage_artifact` içine üç rapor yazılmalı ve hepsi metadata’dan izlenebilir olmalı:
1. `artifact_contract_report.json` — required artifact var/yok kontratı (R010)
2. `reproducibility_report.json` — same commit+seed tolerans kontrolü (R011)
3. `regression_gate_report.json` — previous successful run’a göre multi-rule pass/fail (R018)

Topoloji (`feature/train/eval_report/artifact`) değişmeden kalmalı; fail semantics stage-level RuntimeError ile enforce edilmeli.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Run geçmişini güvenilir okumak | `run_metadata.json` + `status=succeeded` filtresi | Zaten canonical lifecycle’in kaynağı, ek DB/tracker gerekmez |
| Metric snapshot çıkarımı | `stage_outputs.train.metrics_by_split` + `stage_outputs.eval_report.calibration.calibration_summary` | S03/S04 kontratlarıyla uyumlu, tekrar hesaplama gerektirmez |
| Fail görünürlüğü | `stage_events.jsonl` + persisted JSON reports | Gelecek agent için deterministic triage yüzeyi sağlar |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — canonical topology ve artifact stage hook; S06 wiring için ana seam.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — topology lock contract; stage genişletmesi buna rağmen kırılmamalı.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — calibration summary contract; regression gate input kaynağı.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — eval-stage artifact wiring pattern.

## Constraints

- Stage topology değişemez (`feature`, `train`, `eval_report`, `artifact`).
- Reproducibility breach fail-fast olmalı (R011).
- Regression gate politikası D005 ile uyumlu olmalı (Brier mandatory, calibration degradation fail, AUC informational).

## Common Pitfalls

- **Yanlış baseline seçimi** — reproducibility için aynı commit+seed, regression için en son başarılı run ayrı ele alınmalı.
- **Eksik artifact’ı sessiz geçmek** — contract raporu `missing_artifacts` ile açıkça fail üretmeli.

## Open Risks

- İlk run’larda baseline olmayacağı için gate’ler `skipped` döner; bu durumun raporda açık reason koduyla görünmesi şart.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Python pipeline contracts | debug-like-expert | available |

## Sources

- Artifact/repro/regression ihtiyaçları ve sahiplikler (source: [`.gsd/REQUIREMENTS.md`](../../../../REQUIREMENTS.md)).
- Regression policy (D005) ve reproducibility tolerance (D004) karar kayıtları (source: [`.gsd/DECISIONS.md`](../../../../DECISIONS.md)).
- Canonical stage lock contract (source: [`mania_pipeline/tests/test_run_pipeline_cli.py`](../../../../../mania_pipeline/tests/test_run_pipeline_cli.py)).
- Eval calibration/governance payload surfaces (source: [`mania_pipeline/scripts/run_pipeline.py`](../../../../../mania_pipeline/scripts/run_pipeline.py)).
