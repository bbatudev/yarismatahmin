# Oturum Başı Raporu

## Tarih: 02-03-2026

---

## ⚠️ ÖNEMLİ KURAL

**Kullanıcı ile onay almadan veya konuşulmadan hiçbir göreve başlanmaması gerekiyor.**
**Doğrudan kod yazmaya başlamak yerine, kullanıcı ile görüşerek iletişim halinde çalışılmalı.**

---

## 1. Oturum Başlangıç Analizi

*(Aşağıdaki adımları sırayla yap)*

### Adım 1: Git Commit Analizi (ÖNEMLİ - İLK ADIM)
- [ ] `git log --oneline -10` komutuyla son 10 commit'i kontrol et
- [ ] Her commit için `git show --stat <commit-hash>` ile detayları gör
- [ ] Hangi dosyalar değişti, ne tür değişiklikler yapıldı analiz et
- [ ] Özellikle dikkat et: yeni feature'lar, model değişiklikleri, veri işleme scriptleri

### Adım 2: Progress.md Oku
- [ ] `csv dosyaları analiz/progress.md` dosyasını aç
- [ ] "Yapılacaklar" bölümünü kontrol et
- [ ] "Tespit Edilen Problemler" bölümünü oku

### Adım 3: Günlük Klasörü Oku (Varsa)
- [ ] Dünkü klasörü kontrol et (önceki gün formatında: DD-MM-YYYY)
- [ ] Dünkü raporda "Yarına Devredilenler" bölümünü oku
- [ ] Dünden bitmemiş görevleri listele

### Adım 4: Kapsamlı Analiz Yap
Şunları değerlendir:
- [ ] Son commit'lerde hangi görevler tamamlanmış?
- [ ] Hangi dosyalar eklendi/güncellendi?
- [ ] Progress.md'deki yapılacaklardan hangisi yapıldı?
- [ ] Dünkü rapordan devredilen görevlerden hangisi bitti?
- [ ] Kod tabanında hangi yeni özellikler var?
- [ ] Hangi görevler hala bekliyor?

### Adım 5: Kullanıcıya Detaylı Özet Sun
Şu formatta rapor hazırla:

#### 📊 Son Commit Özeti
- Son 5 commit'te yapılanlar (kısa özet)
- Tamamlanan görevler
- Eklenen/güncellenen dosyalar

#### ✅ Tamamlanan Görevler
- Dünden devralınan görevlerden tamamlananlar
- Progress.md'den tamamlananlar

#### 📋 Bekleyen Görevler
- Dünden devralınan ama bitmemiş görevler
- Progress.md'den yüksek öncelikli görevler
- Orta öncelikli görevler

#### ⚠️ Tespit Edilen Problemler
- Progress.md'deki problemler
- Commit'lerden anlaşılan yeni problemler

### Adım 6: Kullanıcıya Sorular Sor
Analizi tamamladıktan sonra kullanıcıya şunları sor:

1. **"Bugün hangi görevle başlamak istersin?"**
   - Bekleyen görevlerden 2-3 öneri sun
   - Her önerinin neden mantıklı olduğunu açıkla

2. **"Son commit'lerde gördüğüm [X] konusunda devam etmek ister misin?"**
   - Eğer son commit'lerde yarım kalmış bir iş varsa sor

3. **"Progress.md'deki [Y] problemi için çözüm üretmek ister misin?"**
   - Kritik problemlerden birini öner

---

## 2. Son Commit Özeti

### 📊 Son 10 Commit'te Yapılanlar
*(git log --oneline -10 çıktısı buraya)*

- Commit 1: [hash] - [mesaj]
- Commit 2: [hash] - [mesaj]
- Commit 3: [hash] - [mesaj]
- Commit 4: [hash] - [mesaj]
- Commit 5: [hash] - [mesaj]
- Commit 6: [hash] - [mesaj]
- Commit 7: [hash] - [mesaj]
- Commit 8: [hash] - [mesaj]
- Commit 9: [hash] - [mesaj]
- Commit 10: [hash] - [mesaj]

### Mevcut Son 10 Commit (Güncel):
- 7672dd8 - feat: korelasyon analizleri, veri toplama ve doğrulama scriptleri
- 36c6ada - chore: Kiro ve Claude için oturum başlangıç hook'ları güncellendi
- 084d3e5 - Update analiz.txt
- ff35228 - değişken analizi, analiz txt devamı
- c713101 - chore: setup empty data and competition directories
- 280bdd9 - Giriş
- 93dce3a - feat: 26-02-2026 16:45 oturum yonetim sistemi ve saat takibi
- 329b340 - Initial commit

### 📁 Değişen Dosyalar
*(git show --stat ile tespit edilenler)*

- [ ] Hangi dosyalar eklendi?
- [ ] Hangi dosyalar güncellendi?
- [ ] Hangi özellikler geliştirildi?

---

## 3. Dünden Devralınan Görevler

*(Dünkü raporun "Yarına Devredilenler" bölümünden kopyalandı)*

### ✅ Tamamlananlar (Son commit'lerden tespit edildi)
- [ ] Liste buraya gelecek

### ⏳ Devam Edenler
- [ ] Liste buraya gelecek

---

## 4. Bugünün Oturum Hedefleri (Öncelik Sırasıyla)

*(Progress.md ve commit analizine göre belirlenir)*

### 🔴 Yüksek Öncelik (Bugün mutlaka yapılacak)
1. **[Görev 1]** - [Açıklama]
2. **[Görev 2]** - [Açıklama]
3. **[Görev 3]** - [Açıklama]

### 🟡 Orta Öncelik (Zaman olursa yapılacak)
1. **[Görev 1]** - [Açıklama]
2. **[Görev 2]** - [Açıklama]

### 🟢 Düşük Öncelik (İmkân varsa)
1. **[Görev 1]** - [Açıklama]

---

## 5. Devam Eden Görevler (Önceki Oturumdan)

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

* Otomasyon ile oluşturuldu: [Tarih]
* Oturum başlangıcı: [Saat]
* Son 5 commit analiz edildi ✅
* Kullanıcı ile görüşüldü ✅

---

## 8. Kullanıcıya Sorulan Sorular ve Cevaplar

### Soru 1: Bugün hangi görevle başlamak istersin?
**Öneriler:**
- [ ] Öneri 1: [Görev] - [Neden mantıklı]
- [ ] Öneri 2: [Görev] - [Neden mantıklı]
- [ ] Öneri 3: [Görev] - [Neden mantıklı]

**Kullanıcı Cevabı:** [Buraya yazılacak]

### Soru 2: Son commit'lerde gördüğüm [X] konusunda devam etmek ister misin?
**Kullanıcı Cevabı:** [Buraya yazılacak]

### Soru 3: Progress.md'deki [Y] problemi için çözüm üretmek ister misin?
**Kullanıcı Cevabı:** [Buraya yazılacak]

---

## 9. Oturum Planı

**İlk 30 dakika:** Dünden devralınan görevleri bitir
**Orta saat:** Yüksek öncelikli yeni görevler
**Son 30 dakika:** Oturum sonu raporu hazırla

---

## 10. BUGÜN YAPILANLAR (02-03-2026)

### Tamamlanan Görevler

**1. Korelasyon Analizi Doğrulama (Dosyalar 01, 02, 03)**
- ✅ Tüm değerler Python ile manuel olarak hesaplandı ve doğrulandı
- ✅ Dosya 01 (RestDays): Ortalama 3.96 ≈ 3.95 (yuvarlama farkı)
- ✅ Dosya 02 (RestDaysDiff): %100 doğru - tüm değerler eşleşti
- ✅ Dosya 03 (WScore-LScore): %100 doğru - tüm değerler eşleşti

**2. Kritik Düzeltme: Dosya 03 Veri Kaynağı**
- ❌ ESKİ: MNCAATourneyDetailedResults.csv (1,449 maç, 2003-2025)
- ✅ YENİ: MNCAATourneyCompactResults.csv (2,585 maç, 1985-2025)
- Sebep: Tüm analiz dosyaları aynı veri kaynağını kullanmalı
- Sonuç: +1,136 maç eklendi, 18 sezon daha dahil oldu

**3. Yeni Dosya: 08_yuzdesel_analizler.txt**
- ✅ Dosyalar 01, 02, 03'ten tüm yüzdesel bulgular özetlendi
- ✅ Tüm percentiles (%10, %25, %50, %75, %90) eklendi
- ✅ Model için tüm anlamlar çıkarıldı
- ✅ Format düzeltildi (daha okunabilir hale getirildi)

**4. Günlük Rapor: 02-03-2026/gunluk_rapor_2026-03-02.txt**
- ✅ Bugün yapılan tüm çalışmalar detaylıca raporlandı
- ✅ Tüm doğrulama sonuçları kaydedildi
- ✅ Tüm bulgular ve çıkarımlar listelendi

### Önemli Bulgular

**1. RestDaysDiff → NEGATIF FEATURE!**
- %49.9 kazanan DAHA AZ dinlenmiş
- Ortalama RestDaysDiff: -0.86
- Konferans turnuva momentumu teorisi

**2. Paslanma Efekti (Rust Effect)**
- 7+ gün dinlenenler: %48.19 kazanma (en düşük!)
- 3-6 gün dinlenenler: %50.89 kazanma (en yüksek!)
- Back-to-back yapanlar: %48.96 kazanma

**3. Turnuva Karakteri**
- %52.3 maç 10 sayı veya daha az farkla bitiyor
- Tek haneli farklar = Turnuva standardı

### Değişen Dosyalar (02-03-2026)
```
korelasyonlar/01_season_daynum_restdays.txt  (Mar  2 22:53)
korelasyonlar/02_restdaysdiff_target.txt    (Mar  2 22:33)
korelasyonlar/03_wscore_lscore.txt          (Mar  2 22:40)
korelasyonlar/08_yuzdesel_analizler.txt     (Mar  2 22:57) - YENI
02-03-2026/gunluk_rapor_2026-03-02.txt      - YENI
```

### Yarına Devredenler

1. **Dosya 07 Kontrol**: MasseyRankDiff analizi
   - MNCAATourneyDetailedResults.csv (1,449 maç) kullanıyor
   - CompactResults'a (2,585 maç) geçirilmeli
   - Massey Ordinals verisinin tam dönem kapsamını kontrol et

2. **Model Feature Mühendisliği**
   - RestDaysDiff (negatif feature!)
   - WScore/LScore percentiles (normalization)
   - PointDiff distribution

---

*Oturum Başlangıcı: -*
*Planlanan Bitiş: -*
*Not: Her değişiklikte saati not al!*
