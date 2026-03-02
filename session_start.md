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
- [ ] `git log --oneline -5` komutuyla son 5 commit'i kontrol et
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

### 📊 Son 5 Commit'te Yapılanlar
*(git log --oneline -5 çıktısı buraya)*

- Commit 1: [hash] - [mesaj]
- Commit 2: [hash] - [mesaj]
- Commit 3: [hash] - [mesaj]
- Commit 4: [hash] - [mesaj]
- Commit 5: [hash] - [mesaj]

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

*Oturum Başlangıcı: -*
*Planlanan Bitiş: -*
*Not: Her değişiklikte saati not al!*
