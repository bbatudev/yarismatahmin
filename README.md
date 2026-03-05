# 🏀 NCAA March Mania 2026 — ML Pipeline

Kaggle March Machine Learning Mania 2026 yarışması için geliştirilmiş makine öğrenmesi pipeline'ı.

## 📁 Proje Yapısı
```
ML_March_Mania2026_NCAA/
├── mania_pipeline/
│   ├── CLAUDE.md                    # Pipeline kuralları ve kısıtlar
│   ├── environment.yml              # Conda ortamı
│   ├── artifacts/
│   │   └── data/
│   │       ├── processed_features_men.csv    # Erkekler işlenmiş veri
│   │       └── processed_features_women.csv  # Kadınlar işlenmiş veri
│   ├── data/
│   │   └── raw/                     # Kaggle ham verisi (git'te yok)
│   └── scripts/
│       └── 02_feature_engineering.py
└── yarismatahmin/                   # Araştırma notları ve analizler
```

## 🎯 Hedef

NCAA turnuva maçlarının sonuçlarını Brier Score metriği ile minimize edecek şekilde tahmin etmek.

## 🔬 Kullanılan Özellikler

- **Seed Farkı** — Turnuva seed numaraları arasındaki fark
- **Massey Consensus** — Elite sistemler (POM, SAG, NET, BPI, MOR, KPI) ortalaması
- **TrueMargin** — Ev sahibi avantajı (5.73) nötrleştirilmiş sayı farkı
- **Four Factors** — eFG%, TOV%, ORB%, FTr (Dean Oliver formülü)
- **Rolling Form** — Son 7/14/21 maç momentum göstergeleri
- **Net Rating** — 100 possession başına sayı farkı
- **Fatigue Flags** — Is_Rusty, Is_Back_To_Back

## ⚙️ Kurulum
```bash
conda env create -f mania_pipeline/environment.yml
conda activate march_mania
```

## 🚀 Pipeline
```bash
# Feature Engineering
python mania_pipeline/scripts/02_feature_engineering.py

# Model Training (yakında)
python mania_pipeline/scripts/03_lgbm_train.py
```

## 📊 Veri Seti

| | Erkekler | Kadınlar |
|---|---|---|
| Satır | 2,898 | 1,922 |
| Özellik | 30 | 27 |
| Min Sezon | 2003 | 2010 |
| Null | 0 | 0 |
| Target Dağılımı | 0.5/0.5 | 0.5/0.5 |

## 🛡️ Kritik Kurallar

- ❌ Zaman sızıntısı (Time Leakage) — kesinlikle yok
- ✅ Walk-Forward CV — Train ≤2022 / Val 2023 / Test 2024-2025
- ✅ Turnuva öncesi snapshot (DayNum < 134)
- ✅ Simetrik hedef (Win=1 / Loss=0)

## 🤖 Modeller (Planlanan)

- LightGBM
- Logistic Regression
- Ensemble (ağırlıklı ortalama)

## 📈 Metrik

**Brier Score** — düşük = daha iyi

---

*Kaggle March Machine Learning Mania 2026*
