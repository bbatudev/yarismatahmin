# M002/S01 — Research

**Date:** 2026-03-15

## Summary

S01 için en düşük-risk seam yine `stage_eval_report`: bu katman model+feature frame üzerinden split bazlı olasılık davranışını zaten hesaplıyor ve artifact üretimi hazır. Drift/rejim sinyalini ayrı stage açmadan burada üretmek topology sözleşmesini korur.

Rejim tanımını ilk iterasyonda basit ve deterministic tutmak kritik. Veri içinde hazır bulunan `SeedNum_diff` sinyali üzerinden `close|medium|wide` segmentasyonu, hem Men hem Women için stabil bir başlangıç sağlıyor. Bu segmentler üzerinden `sample_count`, `pred_mean`, `actual_rate`, `gap` ve split-train karşılaştırmalı delta ile alert üretebiliriz.

## Recommendation

S01’de `drift_regime_report.json` üret:
- split seviyesinde: Train/Val/Test summary
- regime seviyesinde (özellikle Test): `close|medium|wide` behavior
- alert flags: `test_gap_shift`, `low_sample_regime`

Payload mirror:
- `eval_report.json.drift`
- `run_metadata.json.stage_outputs.eval_report.drift`

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Split/gender scoring | `stage_eval_report` içindeki mevcut rescoring loop | Drift için ek scoring altyapısı yazmaya gerek yok |
| Artifact emission | `_write_json` + run_dir conventions | Contract yüzeyleri ile uyumlu kalır |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py::_build_calibration_rows_and_summary` — split bazlı metric/diagnostic pattern.
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py` — eval artifact contract test şablonu.
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py` — eval payload genişletme pattern’i.

## Constraints

- Canonical stage topology değişmez.
- Drift sinyalleri deterministic olmalı; rastlantısal sampling yok.
- Rapor aggregate seviyede kalmalı, row-level prediction persist edilmemeli.

## Common Pitfalls

- **Regime sparse bins** — düşük örnekli segmentleri hard-fail yapmak yerine reason-coded alert üretmek daha güvenli.
- **Overfitted threshold** — ilk iterasyonda sabit, muhafazakar eşikler kullan.

## Open Risks

- Seed dağılımı seasons arası değiştiğinde regime alert’leri false-positive üretebilir; S02’de policy coupling ile yeniden kalibre edilmeli.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Contract debugging | debug-like-expert | available |

## Sources

- M002 hedef/kısıtlar (source: [`.gsd/milestones/M002/M002-CONTEXT.md`](../M002-CONTEXT.md)).
- Eval-stage contract pattern (source: [`mania_pipeline/scripts/run_pipeline.py`](../../../../../mania_pipeline/scripts/run_pipeline.py)).
- Calibration/governance artifact tests (source: [`mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`](../../../../../mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py), [`mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py`](../../../../../mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py)).
