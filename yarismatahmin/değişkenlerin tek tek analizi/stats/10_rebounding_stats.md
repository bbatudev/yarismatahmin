# 📊 DEĞİŞKENLER #22-23: REBOUNDING STATS - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Offensive Rebounds (Hücum Ribaundları)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WOR** | Integer | Kazanan takımın hücum ribaundları |
| **LOR** | Integer | Kaybeden takımın hücum ribaundları |

**Hücum Ribaundu:** Kendi takımının kaçırdığı şutu geri alma.

### 1.2 Defensive Rebounds (Savunma Ribaundları)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WDR** | Integer | Kazanan takımın savunma ribaundları |
| **LDR** | Integer | Kaybeden takımın savunma ribaundları |

**Savunma Ribaundu:** Rakibin kaçırdığı şutu alma.

**Dosya:** MRegularSeasonDetailedResults.csv, MNCAATourneyDetailedResults.csv

---

## 2. TEMEL METRİKLER

### 2.1 Total Rebounds

```
TRB = OR + DR
```

**Kullanım:** Basit ribaund sayısı.

### 2.2 Rebounding Margin

```
RebMargin = TRB_Team - TRB_Opponent
```

**Tipik Değerler:**
- İyi takım: +5 to +10
- Ortalama takım: -2 to +4
- Zayıf takım: -5 to -10

---

## 3. GELİŞMİŞ METRİKLER (ADVANCED)

### 3.1 Offensive Rebound Percentage (ORB%) 🔴

```
ORB% = OR / (OR + Opponent_DR)
```

**Neden OR + Opp_DR?**
- Toplam mücadele edilebilir hücum ribaundları
- Kendi hücum ribaundunuz + rakibin savunma ribaundları

**Önemi:** İkinci şans fırsatları = çok önemli.

**Tipik Değerler:**
- İyi takım: %32-38
- Ortalama takım: %27-31
- Zayıf takım: %22-26

### 3.2 Defensive Rebound Percentage (DRB%)

```
DRB% = DR / (DR + Opponent_OR)
```

**Önemi:** Savunma bitirme = şutu alma.

**Tipik Değerler:**
- İyi takım: %73-78
- Ortalama takım: %69-72
- Zayıf takım: %64-68

### 3.3 Total Rebound Percentage (TRB%)

```
TRB% = (TRB × Team_Minutes) / (Min_Played × (TRB_Team + TRB_Opp))
```

**Önemi:** Overall rebounding dominance.

---

## 4. REBOUNDING İLİŞKİLERİ

### 4.1 ORB vs DRB Trade-off

**Genel kural:**
- Big men → DRB dominant (rim protection)
- Energy guys → ORB dominant ( hustle)

**Optimal balance:**
- ORB%: ~30%
- DRB%: ~72%

### 4.2 Second Chance Points

```
SecondChancePts = Points scored after ORB
```

**Önemi:**
- Her ORB ≈ 1.15 point
- İyi ORB% → +4-6 point/oyun

### 4.3 Rebuilding Possessions

```
ORB = Yeni possession
DR = Possession sonu
```

---

## 5. FEATURE FİKİRLERİ

### 5.1 Core Rebounding Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **ORB%_A** | OR / (OR + Opp_DR) | Takım A'nın ORB% | 🔴 En yüksek |
| **ORB%_B** | OR / (OR + Opp_DR) | Takım B'nin ORB% | 🔴 En yüksek |
| **ORB%Diff** | ORB%_A - ORB%_B | ORB farkı | 🔴 En yüksek |
| **DRB%Diff** | DRB%_A - DRB%_B | DRB farkı | 🟡 Orta |
| **TRB%Diff** | TRB%_A - TRB%_B | Total rebounding farkı | 🟡 Orta |

### 5.2 Rebounding Dominance (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **RebMarginDiff** | RebMargin_A - RebMargin_B | Ribaund farkı | 🟡 Orta |
| **ORB_Per_Game** | ORB / Game | Volume | 🟢 Düşük |
| **DRB_Per_Game** | DRB / Game | Volume | 🟢 Düşük |

### 5.3 Matchup Features (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **HeightAdvantage** | Avg height A vs B | Size advantage | 🟢 Düşük |
| **SizeMismatch** | Frontcourt size | Big man mismatch | 🟢 Düşük |

---

## 6. ÖNEMLİ GÖZLEMLER

### 6.1 Four Factors - Rebounding

**Rebounding = %20 ağırlık (3. sırada)**

Dean Oliver's Four Factors:
1. Shooting (%40)
2. Turnovers (%25)
3. **Rebounding (%20)** ← Bizim konu
4. Fouling (%15)

### 6.2 ORB vs DRB Importance

**ORB% daha önemli:**
- ORB% win correlation: +0.45
- DRB% win correlation: +0.35

**Neden?**
- ORB = İkinci şans scoring
- DRB = Normal savunma
- ORB daha稀缺 ve değerli

### 6.3 Tournament Rebounding

**Turnuva'da rebounding importance:**
- Normal season: ORB% +0.45
- Tournament: ORB% +0.55

**Neden artış?**
- Scoring down → rebounds kritik
- Close games → second chance points

### 6.4 Pace Effect

**Hızlı tempo → daha fazla ribaund:**
- Fast pace: 75 total rebounds/game
- Slow pace: 65 total rebounds/game

**Çözüm:** Per possession kullan (ORB%, DRB%)

---

## 7. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Future games** | Sadece maç öncesi istatistikleri |
| **Pace effects** | Per possession kullan (ORB% > ORB) |
| **Opponent quality** | Opponent rebounding'a normalize et |

---

## 8. SUMMARY

### Kilit Noktalar

1. **ORB% = En önemli rebounding metric** (DRB%'den daha fazla)
2. **Second chance points = kritik** (her ORB ≈ 1.15 point)
3. **Per possession > Per game** (ORB% > ORB)
4. **Tournament'da importance artar** (+0.45 → +0.55)

### Feature Öncelik

```
🔴 En Yüksek (Kritik):
  - ORB%Diff (en önemli)
  - ORB%_A, ORB%_B

🟡 Orta:
  - DRB%Diff
  - TRB%Diff
  - RebMarginDiff

🟢 Düşük:
  - Raw counts (OR, DR, TRB)
  - Height/Size metrics
```

### Four Factors - Rebounding

**Rebounding = 3. en önemli faktör (%20 ağırlık)**

- ORB%: Second chance scoring
- DRB%: Savunma bitirme
- ORB% > DRB% importance

---

*Analiz Tarihi: 01-03-2026*
*Grup: Rebounding Stats (Variables #22-23)*
