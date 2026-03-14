# S02: Split/Leakage Contract Gates — UAT

**Milestone:** M001
**Written:** 2026-03-14

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: S02 behavior hem contract (payload schema/fail semantics) hem canlı runtime (feature-stage fail-fast + metadata persistence) gerektiriyor; bu yüzden pytest + gerçek CLI smoke birlikte doğrulama için yeterli.

## Preconditions

- Repo root: `C:\Users\Gaming\Desktop\projects\yarismatahmin`
- Python env hazır: `./venv/Scripts/python`
- Kaggle veri dosyaları mevcut (men/women regular season + tournament CSV’leri)
- Yazma izni mevcut: `mania_pipeline/artifacts/runs/`

## Smoke Test

`./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke` komutunu çalıştır. Komut başarıyla biter ve yeni run metadata’sında `stage_outputs.feature.gates.men` ve `.women` alanları doluysa smoke pass.

## Test Cases

### 1. Contract validators deterministic payload üretir

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py`
2. Test çıktısını kontrol et.
3. **Expected:** Tüm testler pass; split mismatch / unknown split label / forbidden leakage column durumlarında `pass=false`, `blocking_rule`, `reason`, `evidence` alanları deterministik üretilir.

### 2. Canonical CLI fail-fast davranışı ve stage stop

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py -k "fail" -vv`
2. İlgili test assertion’larını kontrol et.
3. **Expected:** Test pass; pipeline non-zero döner, `feature` dışındaki stage’ler çalışmaz, failed event `error.message` içinde `blocking_rule` bulunur.

### 3. Pass path metadata persistence + stage order korunumu

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_cli.py`
2. Çalıştır: `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke`
3. Çalıştır:
   `./venv/Scripts/python -c "import json, pathlib; run=max(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s02_split_leakage_smoke'), key=lambda p: p.stat().st_mtime_ns); md=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass']; print('S02 gate metadata contract ok')"`
4. **Expected:** Testler pass; smoke run succeeded; metadata assertion pass ve `S02 gate metadata contract ok` yazdırır.

### 4. Observability surfaces (pass + fail) çalışıyor

1. Pass run metadata’yı aç: `mania_pipeline/artifacts/runs/<latest_s02_split_leakage_smoke>/run_metadata.json`
2. `stage_outputs.feature.gates.{men,women}` altında aggregate payload + nested `evidence.split` / `evidence.leakage` alanlarını doğrula.
3. Fail surface için `test_run_pipeline_split_leakage_gate.py -k "fail"` testinin assertion sonucunu doğrula (failed event error.message içinde `blocking_rule`).
4. **Expected:** Pass run’da gate payload’ları dolu; fail doğrulamasında `feature` stage failed event `blocking_rule` içeriyor.

## Edge Cases

### Unknown split label rejection

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py -k unknown`
2. **Expected:** Test pass; unknown split label durumunda split contract `pass=false` ve blocking rule ile fail eder.

### Forbidden post-game column rejection

1. Çalıştır: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py -k forbidden`
2. **Expected:** Test pass; leakage contract forbidden column tespitinde fail eder ve offending column listesi evidence içinde yer alır.

## Failure Signals

- `run_pipeline.py` smoke komutu non-zero döner ve gate olmayan bir sebeple düşer.
- `run_metadata.json` içinde `stage_outputs.feature.gates` yok veya payload şeması eksik.
- Fail-fast testi geçse bile `blocking_rule` error mesajında görünmüyorsa diagnostics contract kırılmıştır.
- Stage order testlerinde `feature -> train -> eval_report -> artifact` sırası drift ederse S01 contract regress olmuştur.

## Requirements Proved By This UAT

- R002 — Deterministic walk-forward split standard canonical runtime’da enforce ve testlerle doğrulandı.
- R004 — Leakage guardrails canonical runtime’da fail-fast enforce edildi; blocking diagnostics ve metadata evidence doğrulandı.

## Not Proven By This UAT

- R003/R019 — Script/notebook single execution path enforcement (S03 kapsamı).
- R005/R006 — Men/Women unified eval core ve side-by-side metrics summary (S03 kapsamı).
- R007/R008/R009/R010/R011/R012/R018 — Calibration, governance, artifact-contract gate, reproducibility, regression ve submission katmanları (S04+).

## Notes for Tester

- Windows shell’de bazı Türkçe karakterler bozuk görünebilir (encoding); gate contract doğruluğunu etkilemez.
- Fail path canlıda yeniden üretilecekse en güvenli yol ilgili pytest fail senaryosunu çalıştırmaktır; bu test fail artifact/event assertions’ını zaten kilitliyor.
