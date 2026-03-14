---
estimated_steps: 5
estimated_files: 3
---

# T02: Wire canonical train/eval stages to publish metrics table + side-by-side summary

**Slice:** S03 — Unified Men/Women Eval Core + Single Execution Path Enforcement
**Milestone:** M001

## Description

T01 payload’ı tek başına yeterli değil; canonical orchestrator bunu artifact yüzeyine taşımalı. Bu task `run_pipeline.py` içinde train/eval stage wiring’ini günceller ve S03 demo çıktısını (`metrics_table` + `side_by_side_summary`) resmi run artifact’ı haline getirir.

## Steps

1. `stage_train` içinde T01’den gelen payload’ı consume et; per-gender model path, split metrics ve feature snapshot alanlarını `stage_outputs.train` altında persist et.
2. `stage_train` başında `stage_outputs.feature.gates.{men,women}.pass` precondition kontrolü ekle; pass değilse train stage fail-fast dursun.
3. `stage_eval_report` içinde per-gender split metriklerinden normalize `metrics_table` üret ve Test split bazlı Men-vs-Women side-by-side summary satırını ekle.
4. `test_run_pipeline_s03_eval_contract.py` ile yeni eval report şemasını ve gate precondition fail davranışını doğrulayan testleri yaz.
5. Gerekli noktalarda `test_run_pipeline_cli.py` beklentilerini yeni `stage_outputs.train` şemasına göre güncelle.

## Must-Haves

- [ ] `eval_report.json` içinde `metrics_table` satırları `gender/split/brier/logloss/auc` alanlarını taşır.
- [ ] `eval_report.json` içinde Men-vs-Women test kıyasını veren `side_by_side_summary` alanı bulunur.
- [ ] Feature gate pass olmadan train stage’e geçiş yoktur (bypass engellenir).

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s03_unified_eval_smoke`
- `./venv/Scripts/python -c "import json, pathlib; r=max([p for p in pathlib.Path('mania_pipeline/artifacts/runs').iterdir() if p.is_dir()], key=lambda p:p.stat().st_mtime_ns); report=json.loads((r/'eval_report.json').read_text(encoding='utf-8')); assert report['metrics_table']; assert 'side_by_side_summary' in report; print('ok', r.name)"`

## Observability Impact

- Signals added/changed: `stage_outputs.train` artık split-level metrics + feature snapshot taşır.
- How a future agent inspects this: tek noktadan `run_metadata.json` ve `eval_report.json` okunarak Men/Women farkı görülebilir.
- Failure state exposed: gate precondition ihlali train stage failed event mesajında explicit görünür.

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — canonical stage wiring ve artifact yazımı.
- `.gsd/milestones/M001/slices/S02/S02-SUMMARY.md` — gate payload’ın precondition olarak tüketilmesi gerektiği forward intelligence.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — S03 train/eval contract wiring’i.
- `mania_pipeline/tests/test_run_pipeline_s03_eval_contract.py` — eval report schema + precondition davranışı testleri.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — orchestrator contract testlerinin yeni train payload yüzeyiyle uyumlu hali.
