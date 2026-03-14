---
estimated_steps: 5
estimated_files: 4
---

# T02: Implement canonical `run_pipeline` CLI and real-stage wiring

**Slice:** S01 — Canonical Run Orchestrator
**Milestone:** M001

## Description

R001’in çekirdeğini hayata geçir: tek komutla feature → train → eval/report → artifact zincirini koşturan canonical orchestrator. Bu task, mevcut script fonksiyonlarını Python-level çağırarak tek run context altında birleştirir; stage lifecycle event’lerini run-scoped artifact klasörüne yazar; hata durumunda makine-okunur fail sinyali üretir.

## Steps

1. `mania_pipeline/scripts/run_pipeline.py` dosyasında argparse tabanlı CLI (`--seed`, `--run-label`, `--artifacts-root`) ve run context üretimini implemente et.
2. Stage wrapper (`feature`, `train`, `eval_report`, `artifact`) yaz; her stage için `started/succeeded/failed` event’lerini `stage_events.jsonl` olarak append et.
3. `02_feature_engineering.py` ve `03_lgbm_train.py` içindeki mevcut fonksiyonları Python-level çağıracak şekilde wiring kur (gerekirse minimal yardımcı fonksiyon iyileştirmeleri yap).
4. Failure path’i non-zero exit code + error payload ile finalize et; run metadata’yı `run_metadata.json` olarak persist et.
5. README’ye canonical komut kullanımını ve artifact lokasyonunu ekle; ardından test + gerçek smoke run doğrulamasını çalıştır.

## Must-Haves

- [ ] Canonical CLI stage sırasını deterministik olarak uygular.
- [ ] Her run için `run_metadata.json` ve `stage_events.jsonl` oluşur.
- [ ] Stage hata verdiğinde run fail olur ve failure event’i okunabilir biçimde yazılır.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke`
- `./venv/Scripts/python -c "from pathlib import Path; import json; d=sorted(Path('mania_pipeline/artifacts/runs').glob('*'))[-1]; m=json.loads((d/'run_metadata.json').read_text(encoding='utf-8')); e=[json.loads(x) for x in (d/'stage_events.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]; assert m['seed']==42; assert [x['stage'] for x in e if x['status']=='succeeded']==['feature','train','eval_report','artifact']; print('ok', d)"`

## Observability Impact

- Signals added/changed: run metadata + per-stage structured lifecycle events.
- How a future agent inspects this: latest run klasöründe `run_metadata.json` ve `stage_events.jsonl` dosyalarını okur.
- Failure state exposed: stage adı, hata mesajı, zaman damgası ve süre tek yerde görünür.

## Inputs

- `.gsd/milestones/M001/slices/S01/tasks/T01-PLAN.md` — testle kilitlenen contract beklentileri.
- `mania_pipeline/scripts/02_feature_engineering.py` — feature stage fonksiyon sınırı.
- `mania_pipeline/scripts/03_lgbm_train.py` — train/eval stage fonksiyon sınırı.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — canonical CLI entrypoint.
- `README.md` — canonical komut kullanım dokümantasyonu.
- `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` — run context artifact’i.
- `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl` — lifecycle contract artifact’i.
