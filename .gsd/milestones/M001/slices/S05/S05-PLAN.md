# S05: Feature Governance + Controlled Ablation

**Goal:** Canonical run içinde feature kararlarını machine-readable ledger’a bağlamak ve şüpheli gruplar için kontrollü ablation delta’larını (Brier/LogLoss/AUC/Calibration) otomatik üretmek.
**Demo:** `run_pipeline.py` tek komutta `governance_ledger.csv` + `ablation_report.json` üretir; `eval_report.json` ve `run_metadata.json.stage_outputs.eval_report.governance` bu artifact path/özetlerini içerir; stage sırası değişmeden kalır.

## Must-Haves

- Her run sonunda governance ledger artifact’ı zorunlu alanlarla üretilir: `feature`, `group`, `default_action`, `evidence` (R008).
- Controlled ablation raporu şüpheli feature grupları için per-gender ve split-aware delta setini üretir: ΔBrier, ΔLogLoss, ΔAUC, ΔCalibration (ECE/W-MAE + high-prob gap) (R009).
- Governance çıktıları mevcut `eval_report` stage’ine entegre edilir; canonical stage topology (`feature`, `train`, `eval_report`, `artifact`) değişmez.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py mania_pipeline/tests/test_feature_governance_ablation.py mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py`
- `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`
- `./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s05_governance_smoke`
- `./venv/Scripts/python -c "import json, pathlib; runs=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s05_governance_smoke')); assert runs, 'no run'; run=runs[-1]; md=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); er=json.loads((run/'eval_report.json').read_text(encoding='utf-8')); gov=md['stage_outputs']['eval_report']['governance']; assert pathlib.Path(gov['artifacts']['ledger_csv']).exists(); assert pathlib.Path(gov['artifacts']['ablation_report_json']).exists(); assert er['governance']['summary']['executed_group_count'] >= 1; print('S05 governance contract ok:', run.name)"`
- `./venv/Scripts/python -c "import json, pathlib; runs=sorted(pathlib.Path('mania_pipeline/artifacts/runs').glob('*_s05_governance_smoke')); assert runs, 'no run'; run=runs[-1]; md=json.loads((run/'run_metadata.json').read_text(encoding='utf-8')); summary=md['stage_outputs']['eval_report']['governance']['summary']; assert 'skipped_groups' in summary and isinstance(summary['skipped_groups'], list); allowed={'group_missing','no_gender_features','split_empty','empty_high_prob_band'}; bad=[g for g in summary['skipped_groups'] if g.get('reason') not in allowed]; assert not bad, f'invalid skip reasons: {bad}'; print('S05 diagnostics contract ok:', run.name)"`

## Observability / Diagnostics

- Runtime signals: `stage_outputs.eval_report.governance.summary` içinde `selected_group_count`, `executed_group_count`, `skipped_groups`, `default_action_counts` alanları.
- Inspection surfaces: `mania_pipeline/artifacts/runs/<run_id>/governance_ledger.csv`, `ablation_report.json`, `eval_report.json`, `run_metadata.json`, `stage_events.jsonl`.
- Failure visibility: ablation skip/failure reason code’ları (`group_missing`, `no_gender_features`, `split_empty`, `empty_high_prob_band`) artifact ve metadata’da açıkça yazılır.
- Redaction constraints: hiçbir row-level prediction veya secret run metadata’ya yazılmaz; evidence aggregate metriklerle sınırlı tutulur.

## Integration Closure

- Upstream surfaces consumed: `stage_outputs.train.genders.*.{model_path,metrics_by_split,feature_snapshot}`, `_build_calibration_rows_and_summary(...)`, `train_baseline(...)`.
- New wiring introduced in this slice: `stage_eval_report` governance builder + ablation runner + artifact emission + metadata/eval wiring.
- What remains before the milestone is truly usable end-to-end: S06’da governance/ablation deltasının regression gate kararına bağlanması.

## Tasks

- [x] **T01: Build governance ledger contract from canonical train payload** `est:1h`
  - Why: R008’in zorunlu ledger alanlarını deterministic ve split-aware evidence ile üretmeden controlled ablation seçimi güvenilir olmaz.
  - Files: `mania_pipeline/scripts/feature_governance.py`, `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_feature_governance_ledger.py`, `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py`
  - Do: Feature group sınıflandırma + default_action policy helper’ını yaz; Men/Women feature namespace farkını gender-aware işle; ledger satırlarını required schema ile üret ve CSV yazım sözleşmesini testle.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ledger.py`
  - Done when: Ledger her feature için `feature/group/default_action/evidence` alanlarıyla üretiliyor ve default_action yalnızca `keep|drop|candidate` değerlerini alıyor.

- [x] **T02: Implement controlled ablation retrain and delta report schema** `est:1h30m`
  - Why: R009 çoklu delil gerektiriyor; baseline metrik tek başına karar üretemez, şüpheli grup için subset retrain delta’sı şart.
  - Files: `mania_pipeline/scripts/feature_governance.py`, `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_feature_governance_ablation.py`, `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py`, `mania_pipeline/scripts/03_lgbm_train.py`
  - Do: Suspicious group seçim kuralını deterministic tanımla (seed + cap); grup bazlı kolon düşürüp `train_baseline(..., random_state=seed)` ile yeniden eğit; Val/Test için ΔBrier/ΔLogLoss/ΔAUC + ΔCalibration (ECE/W-MAE/high-prob gap) hesaplayıp `ablation_report.json` şemasını doldur.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_feature_governance_ablation.py`
  - Done when: `ablation_report.json` her çalıştırılan grup için required delta metriklerini içeriyor; çalıştırılamayan gruplar reason-code ile açıkça işaretleniyor.

- [x] **T03: Wire governance artifacts into eval report + metadata and prove runtime contract** `est:1h`
  - Why: Slice demo yalnızca artifact üretmek değil; canonical run tüketicilerinin (`eval_report`, `stage_outputs`) bu yüzeyi stabil görmesi gerekiyor.
  - Files: `mania_pipeline/scripts/run_pipeline.py`, `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py`, `mania_pipeline/tests/test_run_pipeline_cli.py`, `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`, `mania_pipeline/artifacts/runs/<run_id>/eval_report.json`, `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json`
  - Do: `stage_eval_report` çıkışına `governance` payload’ı (artifact path + summary + diagnostics) ekle; mevcut calibration contract’ını bozmadan JSON yapısını genişlet; topology-lock testini koruyup yeni contract assertion testlerini ekle; canonical smoke run ve script assert ile artifact varlığını doğrula.
  - Verify: `./venv/Scripts/python -m pytest mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py mania_pipeline/tests/test_run_pipeline_cli.py mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py && ./venv/Scripts/python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label s05_governance_smoke`
  - Done when: Son smoke run’da governance artifact path’leri metadata/eval içinde görünüyor, tüm S05 testleri geçiyor, canonical stage listesi değişmemiş kalıyor.

## Files Likely Touched

- `mania_pipeline/scripts/run_pipeline.py`
- `mania_pipeline/scripts/feature_governance.py`
- `mania_pipeline/scripts/03_lgbm_train.py`
- `mania_pipeline/tests/test_feature_governance_ledger.py`
- `mania_pipeline/tests/test_feature_governance_ablation.py`
- `mania_pipeline/tests/test_run_pipeline_s05_governance_contract.py`
- `mania_pipeline/tests/test_run_pipeline_cli.py`
- `mania_pipeline/tests/test_run_pipeline_s04_calibration_contract.py`
- `.gsd/milestones/M001/slices/S05/S05-PLAN.md`
