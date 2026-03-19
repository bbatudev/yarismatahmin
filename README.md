# 🏀 NCAA March Mania 2026 — ML Pipeline

Kaggle March Machine Learning Mania 2026 için geliştirilen, **canonical** ve denetlenebilir ML pipeline.

---

## ✅ Güncel Durum (Final Recipe / Kaggle Submission Hazır)

- Canonical akış aktif: `feature -> train -> eval_report -> artifact`
- Pipeline artık gerçek Kaggle submission export üretebiliyor
- Weighted gate, error decomposition, stacking, feature branching, alternative model benchmark ve men-side policy araştırmaları repo içine script-first bağlandı
- Araştırma fazı büyük ölçüde kapandı; aktif faz artık **final recipe + Kaggle packaging**

### Mevcut stratejik sonuç

- **Men final policy:** `TabPFN` tabanlı candidate gerçek runtime’a bağlandı
  - `tabpfn_benchmark: 1.0`
  - high-probability tail için hafif lift guardrail’i uygulanıyor
- **Women final policy:** release-safe blend aktif
  - `spline_logistic_benchmark: 0.75`
  - `tabpfn_benchmark: 0.25`
- Ana plumbing fix tamamlandı:
  - `blend_final_recipe_v1` artık artifact’ta seçilen candidate’ı runtime prediction policy’ye gerçekten bağlıyor
  - placeholder `0.5` submission writer kaldırıldı
  - sample submission ID listesinden gerçek hypothetical matchup inference/export geliyor

### Final release özeti

- Runtime selection bug çözüldü
- Men tarafında en güçlü candidate gerçekten apply edildi
- Women tarafında final blend korunarak kaldı
- Canonical regression gate geçildi
- Gerçek stage2 submission CSV üretildi

### Son canonical final run

- Run:
  - `mania_pipeline/artifacts/runs/20260319T030908Z_final_recipe_dry_run_v14_men_tabpfn_tail_lift`
- Men test Brier:
  - `0.1703277886080936`
- Women test Brier:
  - `0.1208348889006466`
- Regression gate:
  - `passed`

### Son gerçek submission export

- Export run:
  - `mania_pipeline/artifacts/runs/20260319T030908Z_final_recipe_submission_export_v3`
- Output:
  - `submission_stage2.csv`
- Validation summary:
  - `row_count = 132133`
  - `min_pred = 0.01359343922477177`
  - `max_pred = 0.9848704811741474`
  - `unique_pred_count = 131838`
  - `exact_half_count = 3`

### Season-by-season backtest (2018–2025, quality_v1)

| Season | Men Test Brier | Women Test Brier |
|---|---:|---:|
| 2018 | 0.20995 | 0.16350 |
| 2019 | 0.18064 | 0.13377 |
| 2021 | skipped | skipped |
| 2022 | 0.22894 | 0.18414 |
| 2023 | 0.20961 | 0.17721 |
| 2024 | 0.20629 | 0.13818 |
| 2025 | 0.15861 | 0.13936 |

- Men mean test brier: `0.19901`
- Women mean test brier: `0.15603`
- 2021 skip nedeni: `val_rows_empty`

Raporlar:
- `mania_pipeline/artifacts/reports/season_backtest_20260315T004012Z.json`
- `mania_pipeline/artifacts/reports/season_backtest_20260315T004012Z.csv`

---

## 📁 Proje Yapısı

```text
ML_March_Mania2026_NCAA/
├── mania_pipeline/
│   ├── scripts/
│   │   ├── run_pipeline.py
│   │   ├── 02_feature_engineering.py
│   │   ├── 03_lgbm_train.py
│   │   ├── compare_run_metrics.py
│   │   └── season_by_season_backtest.py
│   ├── tests/
│   └── artifacts/
└── .gsd/
    └── milestones/
        ├── M004/
        │   ├── M004-SUMMARY.md
        │   ├── S01-BENCHMARK-COMPARISON.json
        │   ├── S03-BENCHMARK-COMPARISON.json
        │   └── S04-FINAL-COMPARISON.json
        └── M005/
            ├── M005-SUMMARY.md
            ├── S04-FEATURE-BRANCH-COMPARISON.json
            ├── S05-BLEND-FOLLOWUP.json
            ├── S06-MEN-POLICY-FOLLOWUP.json
            ├── S07-MEN-COMBO-FOLLOWUP.json
            └── S09-MEN-REGIME-ROUTING-FOLLOWUP.json
```

---

## 🎯 Hedef

NCAA turnuva maçları için iyi kalibre edilmiş olasılık üretip **Brier Score** değerini minimize etmek.

---

## 🔬 Ana Özellik Grupları

- **Seed farkı**
- **Massey Elite Consensus** (POM, SAG, NET, BPI, MOR, KPI)
- **TrueMargin / NetRtg**
- **Four Factors** (eFG%, TOV%, ORB%, FTr)
- **Rolling form** (7/14/21)
- **Fatigue flags**

---

## ⚙️ Kurulum

```bash
conda env create -f mania_pipeline/environment.yml
conda activate march_mania
```

---

## 🚀 Çalıştırma

### Canonical run
```bash
python mania_pipeline/scripts/run_pipeline.py --seed 42 --run-label local_smoke
```

### Canonical research smoke
```bash
python mania_pipeline/scripts/run_pipeline.py \
  --seed 42 \
  --run-label local_smoke
```

### Final recipe dry-run
```bash
python mania_pipeline/scripts/run_pipeline.py \
  --seed 42 \
  --prediction-policy blend_final_recipe_v1 \
  --submission-stage stage2 \
  --run-label final_recipe_dry_run
```

### Export existing final run to real stage2 submission
Bu repo’da final recipe seçimi canonical run üzerinde yapılır; gerçek Kaggle CSV export ise bu run context’inden alınır.

- Canonical final dry-run sonrası:
  - `submission_stage2.csv` gerçek matchup probability’leri ile üretilir
- Output path örneği:
  - `mania_pipeline/artifacts/runs/20260319T030908Z_final_recipe_submission_export_v3/submission_stage2.csv`

### Baseline vs candidate kıyas
```bash
python mania_pipeline/scripts/compare_run_metrics.py \
  --baseline-run mania_pipeline/artifacts/runs_m003/s04_gate/20260314T233640Z_m003_s04_readiness_gate \
  --candidate-run mania_pipeline/artifacts/runs_m004/20260315T001052Z_m004_s04_final_freeze \
  --output-json .gsd/milestones/M004/S04-FINAL-COMPARISON.json
```

### Season-by-season backtest (Men + Women)
```bash
python mania_pipeline/scripts/season_by_season_backtest.py \
  --profile quality_v1 \
  --start-season 2018 \
  --end-season 2025 \
  --quiet-train
```

---

## 📦 Run Artifact’ları

Her canonical run için tipik çıktılar:

- `run_metadata.json`
- `stage_events.jsonl`
- `eval_report.json`
- `artifact_manifest.json`
- `hpo_report.json` (HPO açıksa)
- `ensemble_report.json`
- `alternative_model_report.json`
- `multi_season_weighted_gate_report.json`
- `error_decomposition_report.json`
- `stacking_policy_report.json`
- `feature_branch_report.json`
- `men_external_prior_policy_report.json`
- `men_combo_followup_report.json`
- `men_tabpfn_followup_report.json`
- `men_gate_aware_search_report.json`
- `submission_readiness_report.json`
- `submission_validation_report.json` (submission açıksa)

Final submission export run’ında ayrıca:

- `submission_stage2.csv`
- `submission_validation_report.json`

---

## 🛡️ Kritik Kurallar

- ❌ Time leakage yok
- ✅ Walk-forward split: Train ≤ 2022 / Val 2023 / Test 2024-2025
- ✅ Turnuva öncesi snapshot (`DayNum < 134`)
- ✅ Simetrik target (Win=1 / Loss=0)
- ✅ Script-first authority (notebook training authority yok)

---

## 📈 Not

Repo artık notebook-first değil, denetlenebilir bir research + release sistemi. Bu aşamadaki en önemli fark:

- final candidate runtime’a gerçekten bağlanıyor
- canonical gate ile release kararı veriliyor
- Kaggle için gerçek CSV export script-first üretiliyor

Bu nedenle ana değer artık yeni research dalları açmaktan çok:

- final recipe’yi bozmadan korumak
- gerçek submission export akışını stabil tutmak
- Kaggle operasyonunu doğru yönetmek
