---
estimated_steps: 5
estimated_files: 4
---

# T02: Wire gates into canonical feature stage + fail-fast integration tests

**Slice:** S02 — Split/Leakage Contract Gates
**Milestone:** M001

## Description

T01’de kilitlenen validator kontratlarını canonical orchestrator’a bağlar. Feature stage sonunda men/women gate kontrolü çalışır; fail durumunda run `feature` stage’inde durur ve error payload stage event kontratına akar. Pass durumunda gate sonuçları run metadata’ya persist edilir.

## Steps

1. `run_pipeline.py` içinde feature stage akışına split/leakage gate çağrılarını ekle; men/women için ayrı gate payload üret.
2. Gate fail durumunda `blocking_rule` içeren `RuntimeError` fırlatıp train stage’e geçişi engelle; mevcut lifecycle wrapper’ın failed event yazmasını kullan.
3. Gate pass payload’larını `stage_outputs.feature.gates` altında metadata’da kalıcılaştır.
4. `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` dosyasında fail-fast ve pass-persist senaryolarını CLI seviyesinde test et.
5. `test_run_pipeline_cli.py` stage-order contractının korunmasını doğrula (gerekirse assertion güncelle).

## Must-Haves

- [ ] Gate fail olduğunda pipeline non-zero döner, `feature` stage `failed` event üretir ve error mesajı `blocking_rule` içerir.
- [ ] Gate pass olduğunda `run_metadata.json -> stage_outputs.feature.gates.{men,women}` payload’ları yazılır.
- [ ] Canonical stage order (`feature -> train -> eval_report -> artifact`) contract testleri geçmeye devam eder.

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_cli.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke`
- `./venv/Scripts/python -c "import json, pathlib; run=max(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s02_split_leakage_smoke'), key=lambda p: p.stat().st_mtime_ns); md=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); g=md['stage_outputs']['feature']['gates']; assert g['men']['pass'] and g['women']['pass']; print('gate payload persisted')"`

## Observability Impact

- Signals added/changed: Feature stage output’una gate diagnostics payload’ı eklenir.
- How a future agent inspects this: `run_metadata.json` ve `stage_events.jsonl` üzerinden pass/fail + blocking rule okunur.
- Failure state exposed: `failed_stage=feature`, `error.message` içinde kural adı/reason, gate evidence metadata yüzeyinde kalır.

## Inputs

- `mania_pipeline/scripts/run_pipeline.py` — S01 stage lifecycle ve fail propagation yüzeyi.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — stage order contract seam.
- `.gsd/milestones/M001/slices/S01/S01-SUMMARY.md` — authoritative diagnostics yüzeyleri.
- `.gsd/milestones/M001/slices/S02/tasks/T01-PLAN.md` — validator API ve gate schema.

## Expected Output

- `mania_pipeline/scripts/run_pipeline.py` — feature-stage gate wiring + metadata persistence.
- `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` — S02 integration contract testleri.
- `mania_pipeline/tests/test_run_pipeline_cli.py` — stage order contractının S02 ile birlikte geçerli kaldığını doğrulayan test güncellemeleri.
