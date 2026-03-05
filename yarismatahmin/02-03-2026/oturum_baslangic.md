# Oturum Başı Raporu

## Tarih: 02-03-2026

---

## ⚠️ ÖNEMLİ KURAL

**Kullanıcı ile onay almadan veya konuşulmadan hiçbir göreve başlanmaması gerekiyor.**
**Doğrudan kod yazmaya başlamak yerine, kullanıcı ile görüşerek iletişim halinde çalışılmalı.**

---

## 1. Progress MD Özeti

*(Aşağıdaki adımları sırayla yap)*

### Adım 1: Progress.md Oku
- [x] `csv dosyaları analiz/progress.md` dosyasını aç
- [x] "Yapılacaklar" bölümünü kontrol et
- [x] "Tespit Edilen Problemler" bölümünü oku

### Adım 2: Günlük Klasörü Oku (Varsa)
- [x] Dünkü klasörü kontrol et (01-03-2026/)
- [x] Dünkü raporda "Yarına Devredilenler" bölümünü oku
- [x] Dünü bitmemiş görevleri listele

### Adım 3: Bugünkü Öncelikleri Çek (Progress'den)
- [ ] Progress.md'den "⏳ Yapılacaklar" tablosunu kopyala
- [ ] En yüksek öncelikli (🔴) görevleri bugüne ata
- [ ] Orta öncelikli (🟡) görevleri zaman kalanlara ata

### Adım 4: Son Commitleri Kontrol Et
- [ ] `git log --oneline -10` çalıştır
- [ ] Son 2-3 commit'in detaylarını `git show --stat` ile gör
- [ ] Hangi dosyalar eklendi/güncellendi, not al
- [ ] Feature engineering, model vb. kodlar yazılmış mı kontrol et

### Adım 5: Kullanıcıya Soru Sor
- [ ] Hook tamamlanıp özet sunulduktan sonra kullanıcıya sor:
  **"Bugün ne yapmak istersin?"**
  - Seçenekleri sun (korelasyon analizi, model eğitimi, EDA vb.)

---

## 2. Dünden Devralınan Görevler

*(Dünkü raporun "Yarına Devredilenler" bölümünden kopyalandı)*

- [x] ~~Veri yükleme script'i yaz (Python)~~ - 02_feature_engineering.py ile yapıldı ✅
- [x] ~~Feature engineering implementation~~ - 02_feature_engineering.py ile yapıldı ✅
- [ ] Korelasyon analizi - Feature'lar arası ilişkileri keşfet
- [ ] Baseline model oluştur (Logistic Regression)
- [ ] Model geliştirme (XGBoost/LightGBM)

---

## 3. Bugünün Oturum Hedefleri (Öncelik Sırasıyla)

### 🔴 Yüksek Öncelik (Bugün mutlaka yapılacak)
1. **Korelasyon analizi** - Feature'lar arası ilişkiler, heat map, önemli ilişkileri tespit et
2. **Baseline model oluştur** - Logistic Regression ile başlangıç modeli
3. **Model eğitimi ve değerlendirme** - Brier Score ile performans ölçümü

### 🟡 Orta Öncelik (Zaman olursa yapılacak)
1. **EDA (Exploratory Data Analysis)** - Veri dağılımları, korelasyonlar, outlier analizi
2. **Model geliştirme (XGBoost/LightGBM)** - Gelişmiş modelleri dene
3. **Hyperparameter tuning** - GridSearch / Optuna ile optimizasyon
4. **Cross-validation stratejisi** - Time-series split ile sezon bazlı CV
5. **Probability calibration** - Brier Score için olasılık kalibrasyonu

### 🟢 Düşük Öncelik (İmkân varsa)
1. **Ensemble modeller** - Birden fazla modeli birleştir
2. **Error analysis** - Hatalı tahminleri analiz et
3. **Final submission** - Kaggle'a dosya yükle

---

## 4. Devam Eden Görevler (Önceki Oturumdan)

*(Devam eden görev bulunamadı - dünden devralınanlar Yukarıda)*

---

## 5. Bilinmesi Gereken Problemler

*(Progress.md'deki "Tespit Edilen Problemler" bölümünden kopyala)*

### 🔴 Yüksek Öncelikli Problemler
| Problem | Çözüm Önerisi |
|---------|---------------|
| **Brier Score için kalibrasyon gerekliliği** | Model olasılıkları 0-1 arası iyi dağıtılmalı |
| **Data leakage riski** | Season < Target AND DayNum < Target kuralı |
| **Cross-validation stratejisi** | Aynı sezonun train ve test setinde olmaması gerekli |
| **Turnuva verisi azlığı** | Sadece turnuva maçları ile model eğitmek yetersiz olabilir |

### 🟡 Orta Öncelikli Problemler
| Problem | Çözüm Önerisi |
|---------|---------------|
| **2020 sezonu yok** (COVID-19) | Veride boşluk var, continuity sorun olabilir |
| **Erkek ve Kadın verileri ayrı** | Ayrı model mi yoksa ortak mı kullanılacak karar verilmeli |
| **Çok fazla sıralama sistemi** (Massey) | Hangi sistemler daha güvenilir, aggregate etme gerekli |
| **Submission ID formatı** | `Season_TeamA_TeamB` formatında, hangi takımın evde olduğu belli değil |

---

## 6. Önemli Hatırlatmalar

**Data Leakage Kuralı (KRİTİK):**
```
Season < Target_Season AND DayNum < Target_DayNum
```

**Train/Test Split:**
```
Train: 2016, 2017, 2018, 2019, 2021, 2022
Val:   2023
Test:  2024, 2025
```

**En Önemli Feature'lar:**
1. SeedDiff (+0.85 korelasyon)
2. MasseyRankDiff (+0.78) - Düşük rank = iyi takım (TERS!)
3. WinPctDiff (+0.70)
4. PointDiffDiff (+0.72)

**Massey Rank Hatırlatma:**
- Düşük rank = iyi takım
- RankDiff = Rank_B - Rank_A (TERS çünkü düşük rank iyi!)

---

## 7. Notlar

* Otomasyon ile oluşturuldu: 02-03-2026
* Oturum başlangıcı: 02-03-2026 20:50
* analiz.txt okundu: 19 dosya, 40+ değişken grubu analiz edildi
* Feature engineering yapıldı (02_feature_engineering.py)
* Sıradaki görev: Korelasyon analizi

---

## 8. Oturum Planı

**İlk 30 dakika:** Dünden devralınan görevleri bitir
**Orta saat:** Yüksek öncelikli yeni görevler
**Son 30 dakika:** Oturum sonu raporu hazırla

---

*Oturum Başlangıcı: -*
*Planlanan Bitiş: -*
*Not: Her değişiklikte saati not al!*
