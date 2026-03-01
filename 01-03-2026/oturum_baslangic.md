# Oturum Başı Raporu

## Tarih: 01-03-2026

---

## 1. Progress MD Özeti

### Adım 1: Progress.md Oku
- [x] `csv dosyaları analiz/progress.md` dosyası açıldı
- [x] "Yapılacaklar" bölümü kontrol edildi
- [x] "Tespit Edilen Problemler" bölümü okundu

### Adım 2: Günlük Klasörü Oku
- [x] 26-02-2026/ klasörü kontrol edildi
- [x] Dünkü raporda "Yarına Devredilenler" bölümü okundu

### Adım 3: Bugünkü Öncelikler
- [x] Progress.md'den "⏳ Yapılacaklar" tablosu kopyalandı
- [x] En yüksek öncelikli (🔴) görevler belirlendi

---

## 2. Dünden Devralınan Görevler

- [ ] Veri yükleme script'i yaz
- [ ] EDA (Exploratory Data Analysis) başlat
- [ ] Baseline model oluştur

---

## 3. Bugünün Oturum Hedefleri (Öncelik Sırasıyla)

### 🔴 Yüksek Öncelik (Bugün mutlaka yapılacak)
1. Veri yükleme ve keşif - Python ile CSV verilerini yükle
2. Baseline model oluştur - Logistic Regression ile başlangıç modeli
3. Feature engineering başlat - Temel özellikleri üret

### 🟡 Orta Öncelik (Zaman olursa yapılacak)
1. EDA (Exploratory Data Analysis) - Veri dağılımları, korelasyonlar
2. Cross-validation stratejisi - Time-series split ile sezon bazlı CV
3. Probability calibration - Brier Score için olasılık kalibrasyonu

### 🟢 Düşük Öncelik (İmkân varsa)
1. Model geliştirme (XGBoost/LightGBM)
2. Hyperparameter tuning
3. Ensemble modeller

---

## 4. Devam Eden Görevler (Önceki Oturumdan)
- [ ] Veri yükleme ve EDA
- [ ] Baseline model
- [ ] Feature engineering

---

## 5. Bilinmesi Gereken Problemler

| Problem | Öncelik |
|---------|---------|
| 2020 sezonu yok (COVID-19) | 🟡 Orta |
| Erkek ve Kadın verileri ayrı - model stratejisi belirsiz | 🟡 Orta |
| Çok fazla sıralama sistemi (Massey) | 🟡 Orta |
| Brier Score için kalibrasyon gerekliliği | 🔴 Yüksek |
| Data leakage riski | 🔴 Yüksek |
| Cross-validation stratejisi belirlenmeli | 🔴 Yüksek |
| Turnuva verisi azlığı | 🔴 Yüksek |

---

## 6. Notlar

- Bugün 1 Mart 2026, proje 26 Şubat'ta başladı
- Proje: March Machine Learning Mania 2026
- Amaç: NCAA basketbol turnuva maçlarını olasılık (0-1) olarak tahmin etmek
- Değerlendirme: Brier Score (düşük daha iyi)
- Environment aktif: venv/ mevcut
- Kaggle linkleri progress.md'de mevcut

---

## 7. Oturum Planı

**İlk 30 dakika:** Dünden devralınan görevleri bitir (veri yükleme script'i)
**Orta saat:** Yüksek öncelikli yeni görevler (baseline model, feature engineering)
**Son 30 dakika:** Oturum sonu raporu hazırla

---

*Oturum Bağlangıcı: __:__*
*Planlanan Bitiş: __:__*
*Not: Her değişiklikte saati not al!*
