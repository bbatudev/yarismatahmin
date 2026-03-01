# Kaggle March Madness 2026 - İş Akışı Planı

## Yarışma Bilgileri

- **Yarışma**: March Machine Learning Mania 2026
- **Amaç**: NCAA basketbol turnuva maçlarının sonucunu olasılık (0-1) olarak tahmin etmek
- **Değerlendirme Metriği**: Brier Score (düşük daha iyi)
- **Format**: `Season_TeamA_TeamB` -> `Pred` (0-1 arası olasılık)

---

## İş Akışı

### 1. Veri Anlama (EDA) 📊

**Amaç**: CSV yapılarını ve ilişkileri anlamak

**Görevler**:
- [ ] Tüm CSV dosyalarını yükle ve incele
- [ ] Hangi sütunların ne işe yaradığını belgele
- [ ] Veri boyutlarını, eksik değerleri kontrol et
- [ ] Sezon aralıklarını belirle (1985-2026)
- [ ] 2020 sezonu durumu (COVID-19)
- [ ] Erkek ve Kadın verilerini karşılaştır

**Önemli Dosyalar**:
- `MTeams.csv` / `WTeams.csv` - Takım bilgileri
- `MNCAATourneyCompactResults.csv` - Turnuva maçları
- `MRegularSeasonDetailedResults.csv` - Normal sezon detayları
- `MMasseyOrdinals.csv` - 196 farklı sıralama sistemi
- `MNCAATourneySeeds.csv` - Turnuva sıralamaları

---

### 2. Feature Engineering 🔧

**Amaç**: Tahmin için kullanılacak özellikleri üret

**Temel Feature'lar**:

| Kategori | Feature'lar |
|----------|-------------|
| **Takım Gücü** | Massey ordinal ortalaması, sıralama farkı |
| **Regular Season** | Win-loss record, point differential, son 10 maç |
| **Seed** | Seed numarası farkı |
| **İstatistikler** | Offensive/defensive efficiency, 3P%, FT% |
| **Konferans** | Konferans gücü, konferans içi performans |

**Data Leakage Önlemleri**:
- [ ] Sadece maç öncesindeki bilgileri kullan
- [ ] Sezon kronolojik sırasını koru
- [ ] Aynı fold içinde gelecekteki maçlardan feature üretme

---

### 3. Baseline Model 🎯

**Amaç**: Basit bir model ile başlangıç skoru al

**Model**: Logistic Regression

**Adımlar**:
- [ ] Temel feature'larla model eğit
- [ ] Zaman-serisi cross-validation (sezonları ayır)
- [ ] Brier Score hesapla
- [ ] Feature importance analiz et

**Değerlendirme**:
- Brier Score (ne kadar düşük o kadar iyi)
- Log Loss
- Accuracy

---

### 4. Model Geliştirme 🚀

**Amaç**: Skoru iyileştirmek için gelişmiş modeller dene

**Modeller**:
- [ ] XGBoost
- [ ] LightGBM
- [ ] Random Forest

**Optimizasyon**:
- [ ] Hyperparameter tuning (GridSearch / Optuna)
- [ ] Feature selection
- [ ] Probability calibration (Brier için kritik!)

---

### 5. Cross-Validation Stratejisi

**Amaç**: Data leakage'dan kaçınarak doğru CV

**Yöntem**: Time-Series Split
- Train: 2016-2022 sezonları
- Val: 2023 sezonu
- Test: 2024-2025 sezonları

**Önemli**: Aynı sezonun train ve test setinde olmaması gerekli

---

### 6. Probability Calibration

**Amaç**: Model olasılıklarını gerçek olasılıklara yakın hale getir

**Neden**: Brier Score olasılık kalitesini ölçüyor

**Yöntemler**:
- Platt Scaling
- Isotonic Regression
- CalibratedClassifierCV

---

### 7. Submission 📤

**Amaç**: Kaggle'a uygun format üret

**Format**:
```
ID,Pred
2025_1101_1112,0.65
2025_1103_1104,0.42
...
```

**Adımlar**:
- [ ] Stage 1 sample submission'ı oku
- [ ] Test seti için tahmin üret
- [ ] CSV formatında kaydet
- [ ] Kaggle'a upload

---

## Riskler ve Çözümler

| Risk | Çözüm |
|------|--------|
| Data leakage | Zaman-serisi CV, feature üretiminde dikkat |
| Turnuva verisi azlığı | Normal sezon verisini de kullan |
| Overfitting | Regularization, early stopping |
| Probability aşırı güveni | Calibration |

---

## Kullanışlı Kaynaklar

- **Kaggle Sayfası**: https://www.kaggle.com/competitions/march-machine-learning-mania-2026
- **Başlangıç Notebook**: https://www.kaggle.com/code/martynaplomecka/march-machine-learning-mania-2026-starter
- **Progress**: [csv dosyaları analiz/progress.md](csv%20dosyaları%20analiz/progress.md)
- **Brainstorm**: [brainstorm_report.md](brainstorm_report.md)

---

*Oluşturulma: 01-03-2026*
*Son Güncelleme: 01-03-2026*
