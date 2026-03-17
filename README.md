# 🏀 NCAA March Mania 2026 — ML Pipeline

Kaggle March Machine Learning Mania 2026 için geliştirilen, **canonical** ve denetlenebilir ML pipeline.

---

## ✅ Güncel Durum (M005 Sonu / Kaggle Hazırlık Fazı)

- Canonical akış aktif: `feature -> train -> eval_report -> artifact`
- Pipeline hâlâ submission-ready omurga olarak çalışıyor
- Weighted gate, error decomposition, stacking, feature branching, alternative model benchmark ve men-side policy araştırmaları repo içine script-first bağlandı
- Araştırma fazı büyük ölçüde tamamlandı; ana faz artık **final recipe + Kaggle packaging**

### Mevcut stratejik sonuç

- **Women:** güçlü non-baseline adaylar bulundu
  - önce `0.6 LGBM + 0.4 HistGB`
  - daha sonra `TabPFN` ve `spline_logistic` ailesi çok güçlü research sinyali verdi
- **Men:** çok sayıda eksen denendi ama clean promotion adayı çıkmadı
  - feature branch
  - blend refinement
  - external-prior / disagreement policy
  - XGBoost / CatBoost / multi-model combos
  - residual correction
  - regime routing
  - TabPFN follow-up
  - gate-aware search
- En güçlü men discipline-safe çizgi şu anda:
  - **`0.5 LGBM + 0.5 HistGB`**

### M005 final okuma

- Pipeline problemi büyük ölçüde çözüldü
- Asıl sınır artık **signal saturation / limited incremental lift**
- Women tarafı research açısından daha verimli çıktı
- Men tarafında ham sinyal bulundu ama bunu canonical, calibration-safe promotion’a çevirmek mümkün olmadı
- Bu yüzden repo’nun doğal devamı artık:
  - final recipe seçimi
  - local final dry-run
  - Kaggle-format packaging
  - Kaggle smoke
  - final submit

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

### Submission-ready smoke
```bash
python mania_pipeline/scripts/run_pipeline.py \
  --seed 42 \
  --training-profile quality_v1 \
  --hpo-trials 2 \
  --hpo-target-profile quality_v1 \
  --submission-stage stage2 \
  --run-label final_readiness_smoke
```

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

Her run için tipik çıktılar:

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

---

## 🛡️ Kritik Kurallar

- ❌ Time leakage yok
- ✅ Walk-forward split: Train ≤ 2022 / Val 2023 / Test 2024-2025
- ✅ Turnuva öncesi snapshot (`DayNum < 134`)
- ✅ Simetrik target (Win=1 / Loss=0)
- ✅ Script-first authority (notebook training authority yok)

---

## 📈 Not

M005 ile repo artık sıradan notebook topluluğu değil, denetlenebilir bir research + release sistemi haline geldi. En önemli sonuç:

- women tarafında gerçek aday sinyalleri var
- men tarafında güçlü raw sinyal var ama clean promotion yok

Bu nedenle bundan sonraki değer, yeni küçük model tweak’lerden çok doğru release disiplini ve Kaggle operasyonundan gelecek.
