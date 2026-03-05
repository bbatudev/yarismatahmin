# 📊 DEĞİŞKEN #1: SEASON

---

## 1. DEĞİŞKEN TANIMI

| Özellik | Değer |
|---------|-------|
| **Değişken Adı** | Season |
| **Tür** | Sayısal (Integer) |
| **Açıklama** | Sezon yılı - Örn: 2025 = 2024-25 akademik yılı |
| **Format** | YYYY (4 haneli yıl) |
| **Benzersiz Değerler** | 42 (erkek), 29 (kadın) |

**Not:** 2025 sezonu = Kasım 2024'den Nisan 2025'e kadar.

---

## 2. VERİ ÖZETİ

| Dosya | Satır Sayısı | Sezon Aralığı | Sezon Sayısı |
|-------|--------------|----------------|--------------|
| MSeasons.csv | 42 | 1985-2026 | 42 |
| WSeasons.csv | 29 | 1998-2026 | 29 |
| MRegularSeasonCompactResults.csv | 196,823 | 1985-2026 | 42 |
| MNCAATourneyCompactResults.csv | 2,585 | 1985-2025 | 40 |
| MRegularSeasonDetailedResults.csv | 122,775 | 1985-2026 | 42 |
| MNCAATourneyDetailedResults.csv | 1,449 | 1985-2025 | 40 |
| MMasseyOrdinals.csv | 5,761,702 | 2003-2026 | 24 |
| MNCAATourneySeeds.csv | 2,626 | 1985-2025 | 40 |

**Turnuva verisi 40 sezon** (2026 turnuvası henüz yapılmadı).

---

## 3. NİÇİN ÖNEMLİ?

### 🔴 Time-Series Split (Kritik)
- Geleceği geçmişle tahmin etme kuralı
- Train: 2016-2022, Val: 2023, Test: 2024-2025
- Asla rastgele split yapma!

### Trend Analizi
Basketbol oyunu zamanla değişti:
| Dönem | Özellik |
|-------|---------|
| 1985-1999 | Yavaş oyun, az 3-point |
| 2000-2014 | Transition dönem |
| 2015+ | 3-point devrimi |

### Cross-Validation
- Season, CV stratejisinin temeli
- K-fold yerine Time-Series Split kullan

---

## 4. FEATURE FİKİRLERİ

| Feature | Açıklama | Önem |
|---------|----------|------|
| **LastSeasonWinPct** | Geçen sezon win oranı | 🔴 Yüksek |
| **Last3SeasonAvg** | Son 3 sezon ortalaması | 🔴 Yüksek |
| **YearOverYearChange** | Yıllık değişim (Current - Prev) | 🟡 Orta |
| **SeasonTrend** | 3 sezon trend (artış/azalış) | 🟡 Orta |
| **RecentSeasonWeight** | Son sezonlara ağırlık | 🟡 Orta |

---

## 5. RİSKLER VE ÇÖZÜMLER

| Risk | Çözüm |
|------|-------|
| **Future Leakage** | Sezon sınırlarına dikkat, sadece geçmiş kullan |
| **Target Leakage** | Sadece maç öncesi bilgilerini kullan |
| **Overfitting** | Minimum 5+ sezon ile eğitim |
| **Concept Drift** | Recent seasons'a daha fazla ağırlık |

### 2020 Sezonu Durumu
- ❌ Yanlış: "2020 sezonu yok"
- ✅ Gerçek: 2020 regular sezon MEVCUT, sadece turnuva iptal

---

## 6. SUMMARY

### Kilit Noktalar
1. **Season = Zaman** → Time-series split şart
2. **Geçmiş → Gelecek** prediction, asla tersi yok
3. **Multi-season train** → Minimum 5+ sezon
4. **2020 verisi var** → Regular sezon oynandı
5. **Concept drift** → Recent seasons daha önemli

### Train/Test Split Örneği
```
Train: 1985-2022 (geçmiş)
Val:   2023
Test:  2024-2025 (gelecek)
```

---

*Analiz Tarihi: 01-03-2026*
*Sonraki Değişken: DayNum*
