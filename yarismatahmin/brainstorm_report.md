# March Machine Learning Mania 2026 - Brainstorm Raporu

## Proje Özeti

Bu Kaggle yarışmasında NCAA basketbol turnuva maçlarını tahmin edeceğiz. Brier Score ile değerlendirilen bir probablistik tahmin modeli geliştirmemiz gerekiyor.

---

## 1. Feature Engineering Fikirleri

### A. Takım Gücü Metrikleri
- **Massey Ordinals Ortalaması**: Tüm sıralama sistemlerinin ortalaması
- **Massey Ordinals Standart Sapması**: Takım performansındaki tutarsızlık
- **Sıralama Trendi**: Sezon sonunda artan/azalan performans
- **Rank Difference**: İki takım arasındaki sıralama farkı

### B. Regular Season Performans
- **Win-Loss Record**: Genel galibiyet yüzdesi
- **Conference Record**: Konferans içindeki performans
- **Strength of Schedule (SOS)**: Oynanan takımların gücü
- **Home/Away Split**: Evde/deplasmandaki performans farkı
- **Last 10 Games**: Sezon sonundaki form
- **Point Differential**: Atılan-alınan basket farkı

### C. İstatistiksel Metrikler
- **Offensive Efficiency**: Her sahadaki sayı ortalaması
- **Defensive Efficiency**: Rakibe verdikleri sayı ortalaması
- **Pace**: Oyun hızı (sahada geçen süre)
- **Turnover Rate**: Top kaybı oranı
- **Rebound Rate**: Hücum/savunma ribauntları
- **3-Point Percentage**: 3 sayı isabeti
- **Free Throw Percentage**: Serbest atış isabeti

### D. Turnuva Geçmişi
- **Historical Tournament Performance**: Geçmiş turnuva başarıları
- **Seed Number**: Turnuva sıralaması
- **Seed Matchup History**: Benzer sıralamalarla geçmiş maçlar
- **Cinderella Factor**: Düşük sıralamalı takımların sürpriz performansı

### E. Coğrafi ve Diğer Faktörler
- **Travel Distance**: Maç yapılacak yerin uzaklığı
- **Rest Days**: Maçlar arası dinlenme süresi
- **Conference Strength**: Konferansın genel gücü
- **RPI (Rating Percentage Index)**: Resmi sıralama metrikleri

---

## 2. Model Yaklaşımları

### A. Basit Modeller (Baseline)
- **Logistic Regression**: Başlangıç için baseline
- **Gradient Boosting**: XGBoost, LightGBM, CatBoost
- **Random Forest**: Feature importance için iyi

### B. İleri Seviye Modeller
- **Neural Networks**: Deep learning ile karmaşık ilişkiler
- **Ensemble Methods**: Birden fazla modelin birleşimi
- **Calibrated Models**: Olasılıkları Brier Score için kalibre etme

### C. Probabilistic Modeller
- **Gaussian Processes**: Belirsizlik quantification
- **Bayesian Methods**: Önceki bilgileri dahil etme
- **Poisson Regression**: Sayı tahmini için

### D. Model Stackleme Önerisi
```
1. XGBoost (gradient boosting)
2. LightGBM (alternatif boosting)
3. CatBoost (categorical features için)
4. Neural Network (karmaşık ilişkiler)
5. Meta-learner (üzerinde ensemble)
```

---

## 3. Veri İşleme Stratejileri

### A. Veri Temizleme
- Missing value imputation (takım bazlı ortalama)
- Outlier treatment (anormal skorlar)
- Data validation (mantıksal tutarlılık)

### B. Feature Scaling
- StandardScaler veya MinMaxScaler
- RobustScaler (outliers için)

### C. Encoding
- One-hot encoding: Conference, Region
- Label encoding: Takım ID'leri
- Target encoding: Kategorik değişkenler için

### D. Time-based Processing
- Sezon içi progression (erken-orta-geç sezon)
- Rolling averages (son 5, 10, 15 maç)
- Momentum indicators

### E. Normalizasyon
- Takım güçlerini normalize etme
- Sıralamaları benzer skalaya getirme
- Fark özellikleri (Team A - Team B) kullanma

---

## 4. Erkek ve Kadın Verileri İşleme

### Ayrı Modelleme (Önerilen)
```
Artıları:
+ Farklı oyun dinamikleri
+ Farklı özellik ağırlıkları
+ Bağımsız optimizasyon
+ Daha iyi interpretability

Eksileri:
- Daha az eğitim verisi
- İki ayrı model bakımı
```

### Birlikte Modelleme
```
Artıları:
+ Daha fazla veri
+ Transfer learning potansiyeli
+ Tek model bakımı

Eksileri:
- Cinsiyet bazlı bias
- Farklı dinamikleri kaybetme
```

### Hibrit Yaklaşım (En İyi)
1. **Paylaşılan Feature Extraction**: Her iki cinsiyet için ortak özellikler
2. **Gender Indicator**: Cinsiyet flag'i ekle
3. **Ayrı Output Layers**: Her cinsiyet için farklı head
4. **Transfer Learning**: Erkek verisiyle eğitip kadına fine-tune

---

## 5. Massey Ordinals Kullanımı

### Temel Yaklaşımlar

**A. Doğrudan Kullanım**
- Son sıralama değeri
- Sıralama farkı (Team A - Team B)
- Sıralama yüzdesi (rank / total_teams)

**B. Türetilmiş Özellikler**
- Sıralama değişimi (sezon başı vs sonu)
- Sıralama trendi (son 5 hafta)
- Çoklu sistem ortalaması
- Sistemler arası uyumsuzluk (std)

**C. Aglomerasyon**
```
- Simple Average: Tüm sistemlerin ortalaması
- Weighted Average: Güvenilir sistemlere ağırlık
- Median: Outliers'dan etkilenmeme
- Truncated Mean: En iyi/kötü sistemleri çıkar
```

**D. Time-weighting**
- Son haftalara daha fazla ağırlık
- Exponential decay (eski sıralamalar azalsın)
- Sliding window (son N hafta)

---

## 6. Cross-Validation Stratejileri

### A. Time-Series Split
```
Önemli: Geleceği geçmişle test etme!
- Sezon 1-3 train
- Sezon 4 validation
- Sezon 5 test (chronological)
```

### B. Sezon Bazlı Split
- Leave-one-season-out: Her sezone göre CV
- Blocking: Aynı sezon içinde leakage önleme

### C. Turnuva Structure Aware
- Turnuva maçları hariç regular season'da CV
- First round, second round ayrı CV
- Benzer seed match'ları CV'de bir arada tut

### D. Group K-Fold
- Group by season (aynı sezon farklı fold'larda)
- Group by conference (konferans leakage önleme)

### E. Custom Validation
```python
# Pseudocode
def custom_cv(data):
    folds = []
    for season in [2016, 2017, 2018, 2019, 2021, 2022, 2023]:
        train = data[data['Season'] < season]
        val = data[data['Season'] == season]
        folds.append((train, val))
    return folds
```

---

## 7. Önemli Riskler ve Dikkat Edilmesi Gerekenler

### A. Data Leakage Riskleri
- **Target Leakage**: Gelecek bilgilerini feature olarak kullanma
- **Temporal Leakage**: Gelecek sezon bilgilerini geçmişe sızdırma
- **Cross-Season Leakage**: CV'de aynı takımın farklı sezonlarını karıştırma

### B. Overfitting Riskleri
- **Seasonal Bias**: Belirli sezonlara overfitting
- **Team Specific**: Belirli takımlara overfitting
- **Small Sample Size**: Turnuva maçları sınırlı

### C. Önemli Dikkat Noktaları
```
1. 2020 sezonu yok (COVID) → continuity issue
2. Kadın verisi farklı formatlarda olabilir
3. Massey sistemleri sezonlar arası değişebilir
4. Turnuva formatı yıllara göre değişebilir
5. Transfer ve koç değişiklikleri hesaba katılmalı
```

### D. Kalibrasyon Riskleri
- **Overconfident Predictions**: 0.99 gibi uç değerler Brier Score'a zarar
- **Underconfident Predictions**: Çok fazla 0.5 değerleri
- Calibration curve kullanarak kontrol

### E. Bias Riskleri
- **Major Conference Bias**: Büyük konferanslara aşırı güven
- **Seed Bias**: Sıralamaya aşırı odaklanma
- **Historical Bias**: Geçmiş trendlerin değişmesi

### F. Pratik Dikkatler
- Missing data handling
- New teams (first time in tournament)
- Roster changes impact
- Injury data (varsa)
- Home court advantage in tournament (neutral sites)

---

## Önerilen Başlangıç Yol Haritası

### Faz 1: Basit Baseline (1-2 gün)
1. Logistic regression ile baseline
2. Sadece rank difference + win-loss record
3. Brier score hesapla

### Faz 2: Feature Engineering (3-5 gün)
1. Tüm özellikleri oluştur
2. Feature importance analizi
3. Correlation matrix

### Faz 3: Model Development (5-7 gün)
1. XGBoost/LightGBM denemeleri
2. Hyperparameter tuning
3. Ensemble başlatma

### Faz 4: Optimization (3-5 gün)
1. Probability calibration
2. Validation stratejisi optimize
3. Error analysis

### Faz 5: Final Polish (2-3 gün)
1. Final ensemble
2. Kaggle submission format
3. Documentation

---

## Başarı İpuçları

1. **Start Simple**: Basitten başla, yavaş yavaş karmaşıklaştır
2. **Validate Properly**: CV stratejisi çok önemli
3. **Calibrate Well**: Brier score için kalibrasyon kritik
4. **Monitor Overfitting**: Public leaderboard'da aşırı uyma
5. **Learn from Past**: Yarışma forumlarını ve geçmiş winner notebook'larını incele

---

*Bu brainstorm raporu, March Machine Learning Mania 2026 projesi için güçlü bir başlangıç noktası sağlamaktadır.*
