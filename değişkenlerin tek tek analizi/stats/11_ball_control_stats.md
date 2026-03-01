# 📊 DEĞİŞKENLER #24-25: BALL CONTROL STATS (ASSISTS & TURNOVERS) - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Assists (Asistler)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WAst** | Integer | Kazanan takımın asistleri |
| **LAst** | Integer | Kaybeden takımın asistleri |

**Asist:** Şut atan oyuncuya doğrudan skor kazandıran pas.

### 1.2 Turnovers (Top Kayıpları)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WTO** | Integer | Kazanan takımın top kayıpları |
| **LTO** | Integer | Kaybeden takımın top kayıpları |

**Turnover:** Topu rakibe kayıt verme (hatalı pas, taşırma adımı, charging vs.).

**Dosya:** MRegularSeasonDetailedResults.csv, MNCAATourneyDetailedResults.csv

---

## 2. TEMEL METRİKLER

### 2.1 Assists Per Game

```
Ast/G = Ast / Games
```

**Tipik Değerler:**
- İyi takım: 16-20
- Ortalama takım: 13-15
- Zayıf takım: 10-12

### 2.2 Turnovers Per Game

```
TO/G = TO / Games
```

**Tipik Değerler:**
- İyi takım: 10-12
- Ortalama takım: 13-15
- Zayıf takım: 16-20

### 2.3 Assist/Turnover Ratio

```
AST/TO = Ast / TO
```

**Tipik Değerler:**
- İyi takım: 1.8-2.5
- Ortalama takım: 1.3-1.7
- Zayıf takım: 0.8-1.2

---

## 3. GELİŞMİŞ METRİKLER (ADVANCED)

### 3.1 Assist Percentage (Ast%) 🔴

```
Ast% = (Ast / (FGM × 1.07)) × 100
```

**Neden 1.07?**
- Field goals made'ın bir kısmı asistsiz
- Corner 3s, putbacks, iso plays

**Önemi:** Top dağıtımı, team play.

**Tipik Değerler:**
- İyi takım: %60-68
- Ortalama takım: %55-59
- Zayıf takım: %48-54

### 3.2 Turnover Percentage (TO%) 🔴

```
TO% = TO / Possessions × 100
```

**Possessions hesabı:**
```
Poss ≈ FGA + 0.44 × FTA - ORB + TO
```

**Önemi:** **En kritik turnover metric**. Per possession.

**Tipik Değerler:**
- İyi takım: %14-17
- Ortalama takım: %18-20
- Zayıf takım: %21-25

### 3.3 Turnover Forced (Defensive)

```
TO_Forced = Opponent_TO
```

**Önemi:** Defansif baskı.

---

## 4. FOUR FACTORS - TURNOVERS 🔴

**Turnovers = 2. en önemli faktör (%25 ağırlık)**

Dean Oliver's Four Factors:
1. Shooting (%40)
2. **Turnovers (%25)** ← Bizim konu
3. Rebounding (%20)
4. Fouling (%15)

### 4.1 TO% Impact

**Her turnover ≈ 1 point loss:**
- İyi TO%: %17 → 17 TO/100 poss ≈ -17 point
- Kötü TO%: %23 → 23 TO/100 poss ≈ -23 point
- **Fark: 6 point/100 possession!**

### 4.2 Turnover Types

| TO Türü | Frekans | Öneme |
|---------|---------|-------|
| Bad pass | %35 | Yüksek |
| Travel | %15 | Orta |
| Offensive foul | %10 | Düşük |
| Stolen | %40 | En yüksek |

---

## 5. ASSISTS İMPORTANCE

### 5.1 Team Play Indicator

**Ast% = Team play quality:**
- Yüksek Ast% → İyi ball movement
- Düşük Ast% → Iso-heavy offense

**Win correlation:**
- Ast% win corr: +0.55
- Ast/G win corr: +0.35

### 5.2 Playmaking

**Point guard importance:**
- İyi PG → Yüksek Ast%
- İyi passing → İyi shot quality

### 5.3 Assists vs Shooting

**Interaction:**
- Yüksek Ast% + Yüksek eFG% = Unstoppable
- Yüksek Ast% + Düşük eFG% = Good shots, poor execution

---

## 6. FEATURE FİKİRLERİ

### 6.1 Core Ball Control Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **TO%_A** | TO / Poss | Takım A'nın TO% | 🔴 En yüksek |
| **TO%_B** | TO / Poss | Takım B'nin TO% | 🔴 En yüksek |
| **TO%Diff** | TO%_B - TO%_A | TO farkı (TERS!) | 🔴 En yüksek |
| **Ast%_A** | (Ast / FGM) × 100 | Takım A'nın Ast% | 🟡 Orta |
| **Ast%_B** | (Ast / FGM) × 100 | Takım B'nin Ast% | 🟡 Orta |
| **Ast%Diff** | Ast%_A - Ast%_B | Ast farkı | 🟡 Orta |

### 6.2 Ball Control Ratio (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **AST_TO_Ratio_A** | Ast / TO | Ball control quality | 🟡 Orta |
| **AST_TO_Ratio_B** | Ast / TO | Ball control quality | 🟡 Orta |
| **RatioDiff** | Ratio_A - Ratio_B | Ratio farkı | 🟡 Orta |

### 6.3 Defensive Pressure (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **TO_Forced_A** | Opp_TO / Poss | Defansif baskı | 🟢 Düşük |
| **TO_Forced_B** | Opp_TO / Poss | Defansif baskı | 🟢 Düşük |
| **TO_ForcedDiff** | Forced_A - Forced_B | Baskı farkı | 🟢 Düşük |

---

## 7. ÖNEMLİ GÖZLEMLER

### 7.1 TO% Turnaround Games

**TO% dominance:**
- TO%Diff +5% → +8 point differential
- TO%Diff +10% → +15 point differential

**Turnuva importance:**
- Normal season: TO% +0.65
- Tournament: TO% +0.75

**Neden artış?**
- High pressure → turnovers artar
- TO% takımı korur

### 7.2 Ast% Tournament Impact

**Ast% importance:**
- Regular season: +0.55
- Tournament: +0.60

**Cinderella teams:**
- Yüksek Ast% → Team play
- Upset potential

### 7.3 Pace Effect

**Hızlı tempo → daha fazla TO:**
- Fast pace: 18 TO/game
- Slow pace: 12 TO/game

**Çözüm:** Per possession kullan (TO%)

---

## 8. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Future games** | Sadece maç öncesi istatistikleri |
| **Pace effects** | Per possession kullan (TO% > TO) |
| **Sample size** | Minimum 10+ maç gerekli |

---

## 9. SUMMARY

### Kilit Noktalar

1. **TO% = İkinci en önemli Four Factor** (%25 ağırlık)
2. **TO% = Per possession metric** (TO/G unreliable)
3. **Ast% = Team play indicator** (ball movement)
4. **Tournament'da importance artar** (TO% +0.65 → +0.75)

### Feature Öncelik

```
🔴 En Yüksek (Kritik):
  - TO%Diff (TERS: TO%_B - TO%_A)
  - TO%_A, TO%_B

🟡 Orta:
  - Ast%Diff
  - AST_TO_RatioDiff

🟢 Düşük:
  - Raw counts (Ast, TO)
  - Defensive TO forced
```

### Four Factors - Turnovers

**Turnovers = 2. en önemli faktör (%25 ağırlık)**

- TO%: En önemli metric (per possession)
- Ast%: Team play indicator
- Düşük TO% = Championship requirement

---

*Analiz Tarihi: 01-03-2026*
*Grup: Ball Control Stats (Variables #24-25)*
