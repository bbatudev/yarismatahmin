# S01: Canonical Run Orchestrator — UAT

**Milestone:** M001
**Written:** 2026-03-14

## UAT Type

- UAT mode: live-runtime
- Why this mode is sufficient: S01’in çıktısı bir CLI orchestrator ve machine-readable artifacts olduğu için doğrulama gerçek veriyle komut çalıştırma + artifact contract kontrolü ile doğrudan yapılabiliyor.

## Preconditions

- Repo root: `C:\Users\Gaming\Desktop\projects\yarismatahmin`
- Python env aktif ve bağımlılıklar kurulu (özellikle `pytest`, `lightgbm`, `pandas`, `numpy`)
- Kaggle CSV verileri repo içindeki beklenen klasörde mevcut (`march-machine-leraning-mania-2026`)
- Yazma izni mevcut: `mania_pipeline/artifacts/runs/`

## Smoke Test

`./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke` komutunu çalıştır. Komut non-zero dönmeden biterse ve yeni run klasöründe `run_metadata.json` + `stage_events.jsonl` oluşursa smoke pass.

## Test Cases

### 1. Contract test suite green

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py mania_pipeline/tests/test_run_pipeline_cli.py`
2. Test raporunu kontrol et.
3. **Expected:** 11 test pass, run context alanları ve lifecycle event schema drift’i yok.

### 2. Canonical CLI full run + stage order

1. Çalıştır: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s01_smoke`
2. Son satırlarda `[OK] run_id=... status=succeeded` çıktısını doğrula.
3. Çalıştır:  
   `./venv/Scripts/python -c "from pathlib import Path; import json; runs=sorted(Path('mania_pipeline/artifacts/runs').glob('*')); latest=runs[-1]; meta=json.loads((latest/'run_metadata.json').read_text(encoding='utf-8')); events=[json.loads(x) for x in (latest/'stage_events.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]; ok=[e for e in events if e.get('status')=='succeeded']; assert {'run_id','seed','git_commit','started_at','command','cwd'}.issubset(meta.keys()); assert [e['stage'] for e in ok]==['feature','train','eval_report','artifact']; print('S01 contract verified:', latest)"`
4. **Expected:** Assertion pass; stage sırası sabit ve metadata required key set tam.

### 3. Observability artifact surfaces present

1. En son run klasörünü belirle: `mania_pipeline/artifacts/runs/<latest_run_id>`
2. Dosyaları kontrol et: `run_metadata.json`, `stage_events.jsonl`, `eval_report.json`, `artifact_manifest.json`
3. **Expected:** Dört dosya da mevcut; `stage_events.jsonl` satırları parse edilebilir JSON.

## Edge Cases

### Stage failure must be machine-readable and stop run

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py -k fail`
2. **Expected:** Test pass; failed stage event’inde `status=failed` ve structured `error` payload bulunur, sonraki stage’ler çalıştırılmaz.

### Seed propagation integrity

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_context_contract.py -k seed`
2. **Expected:** Seed run context ve metadata içine integer olarak yazılır; type drift yok.

## Failure Signals

- `run_pipeline.py` komutu non-zero exit dönüyor.
- `stage_events.jsonl` içinde `feature -> train -> eval_report -> artifact` dışında sıra görülüyor.
- `run_metadata.json` içinde required alanlardan biri eksik (`run_id`, `seed`, `git_commit`, `started_at`, `command`, `cwd`).
- `stage_events.jsonl` parse edilemiyor veya failed event’te `error` boş.

## Requirements Proved By This UAT

- R001 — Canonical end-to-end run command gerçek veriyle tek komutta çalışıyor ve contract check’leri geçiyor.

## Not Proven By This UAT

- R002/R004 — deterministic split ve leakage fail gates henüz bu slice’ta yok.
- R003/R019 — notebook training path enforcement henüz bu slice’ta yok.
- R006/R007/R008/R009/R010/R011/R012/R018 — tam milestone kapsamındaki metrik, calibration, governance, artifact-gate ve regression policy katmanları sonraki slicelarda tamamlanacak.

## Notes for Tester

- Windows terminalinde bazı Türkçe karakterler mojibake görünebilir; bu görsel encoding problemi, contract/artifact doğruluğunu etkilemez.
- Run süresi veri okuma + model eğitimi nedeniyle birkaç on saniye sürebilir.
