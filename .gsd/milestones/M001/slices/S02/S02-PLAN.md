# S02: Split/Leakage Contract Gates

**Goal:** Walk-forward split ve leakage kontratlarını canonical run içinde train başlamadan önce fail-fast enforce etmek.
**Demo:** Canonical run, split/leakage ihlalinde `feature` stage’inde non-zero ile durur; pass durumunda gate sonuçları `run_metadata.json -> stage_outputs.feature.gates` altında gender-bazlı evidence ile yazılır.

## Must-Haves

- R002: Deterministic split contract zorunlu — `Train<=2022`, `Val=2023`, `Test in {2024,2025}` dışında etiket/season eşleşmesi tespit edilirse gate fail verir.
- R004: Leakage contract zorunlu — post-game/raw outcome kaynaklı yasak kolonlar ve split namespace ihlalleri gate fail verir.
- Gate sonucu standart şema ile üretilir ve persist edilir: `pass`, `blocking_rule`, `reason`, `evidence`.
- Fail durumda pipeline `feature` stage’inde durur; `stage_events.jsonl` failed event error mesajı `blocking_rule` içerir.
- S01 stage order contract bozulmaz (`feature -> train -> eval_report -> artifact`).

## Proof Level

- This slice proves: contract + integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_cli.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py -k "fail" -vv` (feature stage fail-fast + `blocking_rule` diagnostics assertion)
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke`
- `./venv/Scripts/python -c "import json, pathlib; run=max(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s02_split_leakage_smoke'), key=lambda p: p.stat().st_mtime_ns); md=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); gates=md['stage_outputs']['feature']['gates']; assert gates['men']['pass'] and gates['women']['pass']; print('S02 gate metadata contract ok')"`

## Observability / Diagnostics

- Runtime signals: `run_metadata.json` altında `stage_outputs.feature.gates.{men,women}` contract payload’ı.
- Inspection surfaces: `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`, `mania_pipeline/artifacts/runs/<run_id>/stage_events.jsonl`.
- Failure visibility: `feature` stage failed event içinde `error.message` üzerinden `blocking_rule` + kısa reason; metadata’da `failed_stage=feature`.
- Redaction constraints: none (secret/PII yok).

## Integration Closure

- Upstream surfaces consumed: `mania_pipeline/scripts/run_pipeline.py` stage lifecycle wrapper, `mania_pipeline/scripts/02_feature_engineering.py` split authority (`assign_split`), existing CLI contract seam (`CANONICAL_STAGES`, `STAGE_HANDLERS`, `main`).
- New wiring introduced in this slice: `feature` stage sonrası men/women dataframe’lerine split+leakage validator uygulanması; gate fail’de `RuntimeError`; gate pass’te metadata persistence.
- What remains before the milestone is truly usable end-to-end: S03’te gate pass state’in unified eval core ile zorunlu bağı ve single execution path enforcement.

## Tasks

- [x] **T01: Implement split/leakage validator contracts + unit tests** `est:1h`
  - Why: R002 ve R004 için deterministic, testlenebilir gate mantığını orchestration’dan bağımsız olarak kilitlemek.
  - Files: `mania_pipeline/scripts/split_leakage_contracts.py`, `mania_pipeline/tests/test_split_leakage_contracts.py`, `mania_pipeline/scripts/02_feature_engineering.py`
  - Do: Split/leakage validator fonksiyonlarını (`validate_split_contract`, `validate_leakage_contract`) standart gate result şemasıyla yaz; split kontrolünde season contiguity dayatma; leakage kontrolünde exact forbidden column set + required namespace contract uygula; unit testlerle pass/fail, `blocking_rule`, `evidence` doğrula.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_split_leakage_contracts.py`
  - Done when: Unit testler split ve leakage fail-path’lerini deterministik olarak doğrular, ihlalde gate payload’ı makine-okunur ve açıklayıcıdır.

- [x] **T02: Wire gates into canonical feature stage + fail-fast integration tests** `est:1h15m`
  - Why: Contract mantığını gerçek canonical runtime’a bağlayıp S02 demosunu (run fail/pass davranışı + metadata persistence) kanıtlamak.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`, `mania_pipeline/tests/test_run_pipeline_cli.py`, `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`
  - Do: `stage_feature` içinde men/women dataframe üretiminden hemen sonra gate’leri çalıştır; fail’de `blocking_rule` içeren `RuntimeError` fırlatıp train stage’e geçişi engelle; pass’de gate payload’larını `stage_outputs.feature.gates` altında persist et; stage order contract testini koruyacak şekilde integration test ekle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py mania_pipeline/tests/test_run_pipeline_cli.py && ./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s02_split_leakage_smoke`
  - Done when: Gate fail senaryosu non-zero + `feature` failed event ile doğrulanır; pass senaryosu metadata’da men/women gate payload’larını içerir; canonical stage order testi geçer.

## Files Likely Touched

- `mania_pipeline/scripts/split_leakage_contracts.py`
- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/scripts/02_feature_engineering.py`
- `mania_pipeline/tests/test_split_leakage_contracts.py`
- `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`
- `mania_pipeline/tests/test_run_pipeline_cli.py`
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md`
- `.gsd/milestones/M001/slices/S02/tasks/T01-PLAN.md`
- `.gsd/milestones/M001/slices/S02/tasks/T02-PLAN.md`
- `.gsd/DECISIONS.md`
- `.gsd/STATE.md`
