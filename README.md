# 🏀 NCAA March Mania 2026 — ML Pipeline

Kaggle March Machine Learning Mania 2026 için geliştirilen, **canonical** ve denetlenebilir ML pipeline.

---

## ✅ Güncel Durum (M004 Sonu)

- Canonical akış aktif: `feature -> train -> eval_report -> artifact`
- Test durumu: **59/59 passed**
- Final readiness: **ready**
- Submission validation (stage2): **passed**
- Final karar: **no_promotion** (M003 baseline performans referansı korunuyor)

### M003 baseline vs M004 final kıyas
(Brier: düşük daha iyi)

- **Men Brier:** `0.1817505 -> 0.1833199` (**+0.001569**, yaklaşık **%0.86 kötüleşme**)
- **Women Brier:** `0.1422320 -> 0.1421470` (**-0.000085**, yaklaşık **%0.06 iyileşme**)
- Basit ortalama Brier değişimi: yaklaşık **%0.46 kötüleşme**

Bu yüzden model promote edilmedi; sadece güvenilirlik/karar mekanizması iyileştirmeleri tutuldu.

---

## 📁 Proje Yapısı

```text
ML_March_Mania2026_NCAA/
├── mania_pipeline/
│   ├── scripts/
│   │   ├── run_pipeline.py
│   │   ├── 02_feature_engineering.py
│   │   ├── 03_lgbm_train.py
│   │   └── compare_run_metrics.py
│   ├── tests/
│   └── artifacts/
└── .gsd/
    └── milestones/
        └── M004/
            ├── M004-SUMMARY.md
            ├── S01-BENCHMARK-COMPARISON.json
            ├── S03-BENCHMARK-COMPARISON.json
            └── S04-FINAL-COMPARISON.json
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

### M004 final smoke (submission dahil)
```bash
python mania_pipeline/scripts/run_pipeline.py \
  --seed 42 \
  --training-profile quality_v1 \
  --hpo-trials 2 \
  --hpo-target-profile quality_v1 \
  --submission-stage stage2 \
  --run-label m004_s04_final_freeze \
  --artifacts-root mania_pipeline/artifacts/runs_m004
```

### Baseline vs candidate kıyas
```bash
python mania_pipeline/scripts/compare_run_metrics.py \
  --baseline-run mania_pipeline/artifacts/runs_m003/s04_gate/20260314T233640Z_m003_s04_readiness_gate \
  --candidate-run mania_pipeline/artifacts/runs_m004/20260315T001052Z_m004_s04_final_freeze \
  --output-json .gsd/milestones/M004/S04-FINAL-COMPARISON.json
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

M004 ile altyapı güvenilirliği ve karar katmanları güçlendirildi (CV-HPO objective, ensemble robustness guard, final freeze proof). Ancak final benchmark kıyasında net performans artışı gelmediği için promotion yapılmadı.
