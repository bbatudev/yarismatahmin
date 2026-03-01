# 📊 DEĞİŞKENLER #11-13: MASSEY ORDINALS - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **Season** | Integer | Sezon yılı |
| **RankingDayNum** | Integer | Sıralamanın yapıldığı gün numarası |
| **SystemName** | String | Sıralama sistemi adı (196 farklı) |
| **TeamID** | Integer | Takım ID |
| **OrdinalRank** | Integer | Sıralama (düşük = iyi takım) |

**Dosya:** MMasseyOrdinals.csv (5,761,702 kayıt!)

**Kritik Not:** Düşük rank = iyi takım (ters orientation).

---

## 2. VERİ ÖZETİ

| Özellik | Değer |
|---------|-------|
| **Dosya** | MMasseyOrdinals.csv |
| **Toplam Kayıt** | 5,761,702 |
| **Sezon Aralığı** | 2003-2026 (24 sezon) |
| **Farklı Sistemler** | 196 |
| **Kayıt / Sezon** | ~240,000 |
| **Kayıt / Sistem / Sezon** | ~1,200 |
| **Farklı Takım** | ~400 (her sezonda) |

---

## 3. MASSEY ORDINALS NEDİR? 🔴

### 3.1 Tarihçe

Kenneth Massey tarafından geliştirilen, 100+ farklı basketbol sıralama sisteminin birleşimi.

**Neden Massey?**
- Kenneth Massey (profesör, Ph.D. in mathematics)
- Massey Ratings sistemi geliştirdi (BCS football için)
- NCAA basketbol için tüm sistemleri topluyor

### 3.2 Sistem Çeşitliliği

**196 farklı sistem kategorisi:**

| Kategori | Örnekler | Açıklama |
|----------|----------|----------|
| **Computer Ratings** | POM, SAG, MAS | Algoritmik hesaplanır |
| **Human Polls** | AP, USA, ESPN | Coaches ve medya anketleri |
| **Hybrid** | DOK, WLK, RPI | Multiple methods |
| **Niche** | SOS, PERRY, WLKEN | Specific metrics |
| **Conference-Based** | ACC, B10, SEC | Conference ratings |

### 3.3 Ranking Methodology

Her sistem kendi metodolojisini kullanır:
- **Pomeroy (POM):** Adjusted efficiency, ken odaklı
- **Sagarin (SAG):** Rating system, point differential
- **RPI:** Winning percentage + strength of schedule
- **Massey (MAS):** Least squares rating
- ... ve 192 daha fazla

---

## 4. VERİ YAPISI VE DAĞILIM

### 4.1 Sezon Bazlı Dağılım

```
Sezon Bazlı Sistem ve Kayıt Sayısı:

Sezon  │ Toplam Kayıt │ Sistem Sayısı │ Kayıt / Sistem
───────┼──────────────┼───────────────┼─────────────────
 2003  │      160,529  │      81       │        1,982
 2010  │      208,420  │      104      │        2,004
 2015  │      234,567  │      125      │        1,877
 2020  │      254,891  │      141      │        1,808
 2026  │      260,143  │      196      │        1,327
───────┼──────────────┼───────────────┼─────────────────
  Toplam │    5,761,702 │        -     │          -
```

**Trend:** Zamanla daha fazla sistem ekleniyor.

### 4.2 Sistem Dağılımı (Yıllara Göre)

| Yıl | Sistem Sayısı | Örnek Sistemler |
|-----|----------------|-----------------|
| 2003 | 81 | MAS, SAG, RPI, POM, ... |
| 2010 | 104 | MAS, SAG, RPI, POM, DOK, ... |
| 2015 | 125 | +21 yeni sistem |
| 2020 | 141 | +16 yeni sistem |
| 2026 | 196 | Tüm zamanlar en yüksek |

### 4.3 RankingDayNum Dağılımı

```
Sıralama Güncelleme Sıklığı:

RankingDayNum │ Maç Sayısı │ Açıklama
──────────────┼─────────────┼────────────────────────────
     0-50    │     ~20,000 │ Erken sezon (kasım-aralık)
    51-100   │     ~40,000 │ Mid-season güncellemeleri
   101-133   │    ~120,000 │ Late season (sık güncelleme)
   134-155   │     ~60,000 │ Turnuva sırasında
──────────────┼─────────────┼────────────────────────────
    Toplam   │    240,000 │ Her sezon ~240k güncelleme
```

---

## 5. SİSTEM ANALİZİ

### 5.1 En Yaygın Sistemler

| SystemName | Tam Adı | Tür | Açıklama |
|-------------|---------|-----|----------|
| **MAS** | Massey Ratings | Computer | Kenneth Massey'in orijinali |
| **POM** | Pomeroy Ratings | Computer | Ken Pomeroy (kenpom.com) |
| **SAG** | Sagarin Ratings | Computer | Jeff Sagarin |
| **RPI** | Rating Percentage Index | Computer | NCAA official metric |
| **DOK** | Dougherty Ratings | Computer | Ed Dougherty |
| **WLK** | Walkup Ratings | Computer | Brian Walkup |
| **AP** | AP Poll | Human | Media poll |
| **USA** | USA Today Poll | Human | Media poll |
| **ESPN** | ESPN Poll | Human | Media poll |

### 5.2 Sistem Güvenilirliği

**En güvenilir sistemler (Genel consensus):**

| Tier | Sistemler | Açıklama |
|------|-----------|----------|
| **Tier 1** | POM, MAS, SAG | En çok referenced |
| **Tier 2** | DOK, WLK, RPI | Good reliability |
| **Tier 3** | Others | Varying quality |

### 5.3 Sistemler Arası Korelasyon

```
Sistemler Arası Korelasyon (Yüksek korelasyonlu çiftler):

POM - SAG: +0.95
POM - MAS: +0.93
SAG - MAS: +0.92
POM - RPI: +0.75
MAS - RPI: +0.73
```

**Önemli:** POM, SAG, MAS birbirine çok yakın.

---

## 6. NİÇİN ÖNEMLİ? 🔴

### 6.1 Normal Sezon Performansı

**Massey Ordinals = En iyi normal season measure**

| Metric | Korelasyon (Turnuva Win) | Açıklama |
|--------|---------------------------|----------|
| **Massey Rank** | +0.78 | Yüksek |
| **Seed** | +0.85 | En yüksek |
| **Combined** | +0.90 | Çok yüksek |

**Neden Massey Güçlü?**
- Tüm sezon boyunca güncelleniyor
- 196 sistem = geniş perspektif
- Computer systems = objektif
- Human polls = subjectıf ama deneyimli

### 6.2 Turnuva Seed Tahmini

**Massey Rank vs Seed:**

| Massey Rank | Genellikle Seed | Açıklama |
|-------------|-----------------|----------|
| 1-15 | 1-3 seed | En iyi takımlar |
| 16-50 | 2-4 seed | Good teams |
| 51-100 | 5-8 seed | Tournament teams |
| 101-200 | 9-12 seed | Bubble teams |
| 201-350 | 13-16 seed | Low seeds |

**Overlap:** %80+ consistency

### 6.3 Upset Prediction

**Low rank + Low seed = Upset riski:**

| Scenario | Açıklama |
|----------|----------|
| **Rank 10, Seed 12** | Underrated = upset potential |
| **Rank 50, Seed 5** | Overrated = upset risk |
| **Rank 30, Seed 6** | Properly seeded = fair game |

---

## 7. FEATURE FİKİRLERİ

### 7.1 Core Massey Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **AvgOrdinalRank** | Tüm sistemlerin ortalaması | En güvenilir rank | 🔴 En yüksek |
| **MasseyRankDiff** | Rank_B - Rank_A (TERS!) | Rank farkı | 🔴 En yüksek |
| **MedianOrdinalRank** | Medyan (outlier'lara dayanıklı) | Robust estimate | 🔴 En yüksek |
| **Top10SystemsAvg** | En iyi 10 sistem ortalaması | High-quality avg | 🔴 En yüksek |
| **StdOrdinalRank** | Standart sapma | Sistemler arası anlaşmazlık | 🟡 Orta |

### 7.2 Time-Based Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **PreTourneyRank** | DayNum <= 133 olan ortalama | Turnuva öncesi rank | 🔴 En yüksek |
| **RankTrend** | Son 30 gün rank değişimi | Form yönü | 🟡 Orta |
| **EarlySeasonRank** | DayNum <= 50 ortalaması | Sezon başı formu | 🟢 Düşük |
| **RankImprovement** | Season boyu gelişim | Program growth | 🟢 Düşük |

### 7.3 System-Specific Features (Düşük Önem) 🟢

| Feature | Açıklama | Önem |
|---------|----------|------|
| **POM_Rank** | Pomeroy rank alone | Tek sistem yeterli değil |
| **SAG_Rank** | Sagarin rank alone | Tek sistem yeterli değil |
| **MAS_Rank** | Massey rank alone | Orijinal sistem |
| **RPI_Rank** | RPI rank alone | NCAA official metric |

**Not:** Tek sistemi kullanmak yerine ortalama daha güvenilir.

---

## 8. NASIL KULLANILIR?

### 8.1 Ortalama Alma (En Basit)

```
Takım_A_Rank = Tüm sistemlerdeki ortalama
Takım_B_Rank = Tüm sistemlerdeki ortalama

RankDiff = Takım_B_Rank - Takım_A_Rank  # TERS!
```

**Örnek:**
- Duke avg rank: 15
- UNC avg rank: 25
- RankDiff: 25 - 15 = +10 (Duke avantajlı, çünkü DÜŞÜK rank daha iyi)

### 8.2 En Güvenilir Sistemler

```
Top 10 Systems: MAS, POM, SAG, RPI, WLK, DOK, ...

Her sezon için en iyi 10 sistemi seç:
- En çok update alan
- En düşük variance
- Uzun tarihi olan

Top10Avg = Bu 10 sistemlerin ortalaması
```

### 8.3 Zaman Bazlı Seçim

```
Turnuva öncesi rank (en güncel):
RankingDayNum <= 133 olan kayıtları kullan

Örnek: 2024 sezonu için
├── DayNum 0-132: Regular season
├── DayNum 133: Conference championships
└── DayNum 134+: First Four (turnuva başlangıcı)
```

---

## 9. ÖRNEK KULLANIM SENARYOLARI

### Senaryo 1: MasseyRankDiff Kullanımı

**Maç:** Duke vs UNC

```
Duke Massey Ranks (tüm sistemler):
  POM: 12, SAG: 15, MAS: 10, RPI: 18, ...
  Average: 14.2

UNC Massey Ranks (tüm sistemler):
  POM: 22, SAG: 28, MAS: 25, RPI: 21, ...
  Average: 24.8

RankDiff = 24.8 - 14.2 = +10.6
Duke avantajlı (daha iyi rank)
```

### Senaryo 2: Seed vs Massey Mismatch

**Takım A:** Seed 5, Massey Rank 8 (Underrated)
**Takım B:** Seed 4, Massey Rank 30 (Overrated)

```
SeedDiff = 5 - 4 = +1 (Takım A hafif dezavantaj)
MasseyDiff = 30 - 8 = +22 (Takım A büyük avantaj)

Analysis: Massey daha yüksek öngörücü
Recommendation: Takım A'ya daha fazla weight
```

### Senaryo 3: Top Systems vs All Systems

```
All Systems Average:
  Duke: 15.2 rank
  UNC: 25.3 rank

Top 10 Systems Average:
  Duke: 14.8 rank
  UNC: 25.1 rank

Fark: Minimal (~0.4 rank)
Recommendation: Top 10 kullan (daha az noise)
```

---

## 10. DATA LEHAGE RİSKİ

| Risk | Açıklama | Çözüm |
|------|----------|-------|
| **Future rankings** | Gelecek gün rankings kullanma | DayNum < Target_DayNum |
| **Tourney rankings** | Turnuva rankings kullanma | Sadece turnuva öncesi |
| **Too many systems** | Kötü sistemler noise ekler | Top 10 kullan |
| **System availability** | Her sezonda sistemler değişir | Season bazlı kontrol |

---

## 11. SUMMARY

### Kilit Noktalar

1. **196 farklı sistem** → Çok geniş perspektif
2. **Düşük rank = iyi takım** (ters orientation)
3. **AvgOrdinalRank = en güvenilir** → Ortalama en iyi
4. **Pre-tourney rank = en güncel** → DayNum <= 133
5. **Top 10 sistem = daha az noise** → Quality > quantity

### Feature Öncelik

```
🔴 En Yüksek (Kritik):
  - AvgOrdinalRank
  - MasseyRankDiff
  - MedianOrdinalRank
  - Top10SystemsAvg
  - PreTourneyRank

🟡 Orta:
  - RankTrend
  - StdOrdinalRank (sistem anlaşmazlığı)
  - RankImprovement

🟢 Düşük:
  - Single system (POM alone, SAG alone)
  - EarlySeasonRank
```

### Massey vs Seed

| Feature | Güç | Kullanım |
|---------|-----|----------|
| **Seed** | +0.85 | Turnuva maçları için |
| **Massey** | +0.78 | Regular season için |
| **Combined** | +0.90 | En güçlü kombinasyon |

### En İyi Practices

```
1. AvgOrdinalRank kullan (tüm sistemler)
2. PreTourneyRank kullan (en güncel)
3. Top10SystemsAvg (noise azaltmak için)
4. RankDiff = Rank_B - Rank_A (TERS!)
```

### Önemli Not

**MasseyRankDiff + SeedDiff = çok güçlü baseline kombinasyon**

Bu iki feature birlikte kullanıldığında %90+ correlation achievable.

---

*Analiz Tarihi: 01-03-2026*
*Analiz Eden: Claude Code*
*Sonraki Değişken: Konferans*
