# 📊 DEĞİŞKENLER #16-21: SHOOTING STATS - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Field Goals (Saha Basketleri)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WFGM** | Integer | Kazanan takımın saha isabeti (Field Goals Made) |
| **WFGA** | Integer | Kazanan takımın saha denemesi (Field Goals Attempted) |
| **LFGM** | Integer | Kaybeden takımın saha isabeti |
| **LFGA** | Integer | Kaybeden takımın saha denemesi |

**Saha Basketi = 2 sayılık atışlar + 3 sayılık atışlar (toplam)**

### 1.2 3-Pointers (3 Sayılıklar)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WFGM3** | Integer | Kazanan takımın 3 sayı isabeti |
| **WFGA3** | Integer | Kazanan takımın 3 sayı denemesi |
| **LFGM3** | Integer | Kaybeden takımın 3 sayı isabeti |
| **LFGA3** | Integer | Kaybeden takımın 3 sayı denemesi |

### 1.3 Free Throws (Serbest Atışlar)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WFTM** | Integer | Kazanan takımın serbest atış isabeti |
| **WFTA** | Integer | Kazanan takımın serbest atış denemesi |
| **LFTM** | Integer | Kaybeden takımın serbest atış isabeti |
| **LFTA** | Integer | Kaybeden takımın serbest atış denemesi |

**Dosya:** MRegularSeasonDetailedResults.csv, MNCAATourneyDetailedResults.csv

---

## 2. TEMEL METRİKLER

### 2.1 Field Goal Percentage (FG%)

```
FG% = FGM / FGA
```

**Önemi:** Temel shooting verimliliği.

**Tipik Değerler:**
- İyi takım: %46-50
- Ortalama takım: %43-45
- Zayıf takım: %40-42

### 2.2 3-Point Percentage (3P%)

```
3P% = FGM3 / FGA3
```

**Önemi:** Perimeter shooting yeteneği.

**Tipik Değerler:**
- İyi takım: %38-42
- Ortalama takım: %34-37
- Zayıf takım: %30-33

### 2.3 Free Throw Percentage (FT%)

```
FT% = FTM / FTA
```

**Önemi:** Clutch situations'da kritik.

**Tipik Değerler:**
- İyi takım: %76-80
- Ortalama takım: %71-75
- Zayıf takım: %65-70

---

## 3. GELİŞMİŞ METRİKLER (ADVANCED)

### 3.1 Effective Field Goal Percentage (eFG%) 🔴

```
eFG% = (FGM + 0.5 × FGM3) / FGA
```

**Neden 0.5?** 3 sayılık atışın değeri 2 sayılığın 1.5 katı.

**Önemi:** 3 sayıları ağırlıklı shooting efficiency. **En önemli shooting metric.**

**Örnek:**
- Team A: 8/20 FG, 4/10 3P → eFG% = (8 + 0.5×4) / 20 = 10/20 = 50%
- Team B: 10/25 FG, 0/5 3P → eFG% = (10 + 0.5×0) / 25 = 10/25 = 40%

### 3.2 True Shooting Percentage (TS%)

```
TS% = Points / (2 × FGA + 0.88 × FTA)
```

**Neden 0.88?** Serbest atışların teknik toplamı (teknik faul vs).

**Önemi:** Tüm scoring verimliliği (FG + FT).

### 3.3 3-Point Rate (3PAR)

```
3PAR = FGA3 / FGA
```

**Önemi:** Takımın play style'ı.

**Tipik Değerler:**
- Modern tempo: %35-45
- Traditional: %25-35
- Inside-heavy: %15-25

### 3.4 Free Throw Rate (FTR)

```
FTR = FTM / FGA
```

**Önemi:** Rakibi faul gönderme yeteneği + FT shooting.

---

## 4. FEATURE FİKİRLERİ

### 4.1 Core Shooting Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **eFG%_A** | Sezon ortalaması | Takım A'nın eFG% | 🔴 En yüksek |
| **eFG%_B** | Sezon ortalaması | Takım B'nin eFG% | 🔴 En yüksek |
| **eFG%Diff** | eFG%_A - eFG%_B | Shooting farkı | 🔴 En yüksek |
| **TS%Diff** | TS%_A - TS%_B | True shooting farkı | 🔴 En yüksek |
| **3P%Diff** | 3P%_A - 3P%_B | 3-point shooting farkı | 🟡 Orta |
| **FT%Diff** | FT%_A - FT%_B | Free throw farkı | 🟡 Orta |

### 4.2 Shooting Volume Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **3PAR_A** | FGA3 / FGA | 3-point deneme oranı | 🟡 Orta |
| **3PAR_B** | FGA3 / FGA | 3-point deneme oranı | 🟡 Orta |
| **3PARDiff** | 3PAR_A - 3PAR_B | Play style farkı | 🟡 Orta |
| **FTRDiff** | FTR_A - FTR_B | FT rate farkı | 🟡 Orta |

### 4.3 Shooting Consistency (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **eFG%Std** | Standart sapma | Shooting consistency | 🟢 Düşük |
| **HotHand** | Son 5 maç eFG% | Recent form | 🟢 Düşük |

---

## 5. ÖNEMLİ GÖZLEMLER

### 5.1 Shooting Efficiency vs Volume

**Trade-off:**
- Yüksek 3PAR = Daha fazla risk
- Düşük 3PAR = Daha stabil ama az scoring

**Optimal:**
- İyi 3P% shooting → Yüksek 3PAR (+)
- Kötü 3P% shooting → Düşük 3PAR (daha fazla inside)

### 5.2 Free Throws in Clutch

**Close games (≤5 point diff):**
- FT% correlation with win: +0.65
- FTM importance: High (garantili point)

### 5.3 Shot Distribution

**Modern Basketball:**
- 3P Rate artışı: %25 (2010) → %40 (2026)
- Mid-range azalması: %20 → %10
- Rim attempts: Stabil (%55)

---

## 6. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Future games** | Sadece maç öncesi istatistikleri |
| **Sample size** | Minimum 10+ maç gerekli |
| **Opponent quality** | Opponent defense'a normalize et |

---

## 7. SUMMARY

### Kilit Noktalar

1. **eFG% = En önemli shooting metric** (3-point ağırlıklı)
2. **Shooting > Volume** → Efficiency > Attempts
3. **3-point revolution** → Modern takımlar daha fazla 3P
4. **Free throws = clutch** → Close game'da kritik

### Feature Öncelik

```
🔴 En Yüksek (Kritik):
  - eFG%Diff
  - TS%Diff

🟡 Orta:
  - 3P%Diff
  - FT%Diff
  - 3PARDiff (play style)
  - FTRDiff

🟢 Düşük:
  - Shooting volume (FGA, FGA3)
  - Consistency metrics
```

### Four Factors - Shooting

**Shooting = En önemli faktör (%40 ağırlık)**

- eFG% = Efficient scoring
- TS% = All-inclusive efficiency
- 3P% = Spacing capability
- FT% = Clutch performance

---

*Analiz Tarihi: 01-03-2026*
*Grup: Shooting Stats (Variables #16-21)*
