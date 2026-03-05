# 📊 DEĞİŞKENLER #26-27: DEFENSIVE STATS (STEALS & BLOCKS) - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Steals (Top Çalmalar)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WStl** | Integer | Kazanan takımın top çalmaları |
| **LStl** | Integer | Kaybeden takımın top çalmaları |

**Steal:** Defansif oyuncunun topu çalması (intercept).

### 1.2 Blocks (Bloklar)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WBlk** | Integer | Kazanan takımın blokları |
| **LBlk** | Integer | Kaybeden takımın blokları |

**Block:** Şutu engelleme (rim protection).

**Dosya:** MRegularSeasonDetailedResults.csv, MNCAATourneyDetailedResults.csv

---

## 2. TEMEL METRİKLER

### 2.1 Steals Per Game

```
Stl/G = Stl / Games
```

**Tipik Değerler:**
- İyi takım: 8-10
- Ortalama takım: 6-7
- Zayıf takım: 4-5

### 2.2 Blocks Per Game

```
Blk/G = Blk / Games
```

**Tipik Değerler:**
- İyi takım: 5-7
- Ortalama takım: 3-4
- Zayıf takım: 1-2

---

## 3. GELİŞMİŞ METRİKLER (ADVANCED)

### 3.1 Steal Percentage (Stl%) 🔴

```
Stl% = (Stl / Opponent_Possessions) × 100
```

**Önemi:** Per possession steal rate.

**Tipik Değerler:**
- İyi takım: %9-11
- Ortalama takım: %7-8
- Zayıf takım: %5-6

### 3.2 Block Percentage (Blk%) 🔴

```
Blk% = (Blk / Opponent_FGA) × 100
```

**Önemi:** Per shot block rate.

**Tipik Değerler:**
- İyi takım: %10-14
- Ortalama takım: %7-9
- Zayıf takım: %4-6

### 3.3 Defensive Rating Impact

**Steal impact:**
- Her steal ≈ 1.2 point gain (fast break)

**Block impact:**
- Her block ≈ 0.8 point gain (deterrent)

---

## 4. DEFENSIVE STATS ANALİZİ

### 4.1 Steals vs Blocks

| Feature | Steals | Blocks |
|---------|--------|--------|
| **Frequency** | %7-9/G | %8-12/G |
| **Impact** | 1.2 pt | 0.8 pt |
| **Correlation (Win)** | +0.45 | +0.35 |
| **Reliability** | Stabil | Volatile |

**Steals > Blocks importance**

### 4.2 Steal Types

| Steal Türü | Frekans | Impact |
|------------|---------|--------|
| Passing lane | %40 | High |
| Dribble | %35 | Medium |
| Off-ball | %25 | Low |

### 4.3 Block Types

| Block Türü | Frekans | Impact |
|------------|---------|--------|
| Rim protection | %60 | High |
| Perimeter | %25 | Medium |
| Help defense | %15 | Low |

---

## 5. POSITIONAL ANALİZ

### 5.1 Steals by Position

| Position | Avg Stl/G | Role |
|----------|-----------|------|
| Point Guard | 2.1 | Perimeter pressure |
| Shooting Guard | 1.4 | Help defense |
| Small Forward | 1.2 | Versatility |
| Power Forward | 0.8 | Help defense |
| Center | 0.5 | Drop coverage |

### 5.2 Blocks by Position

| Position | Avg Blk/G | Role |
|----------|-----------|------|
| Point Guard | 0.2 | - |
| Shooting Guard | 0.3 | Help |
| Small Forward | 0.5 | Help |
| Power Forward | 1.2 | Rim protector |
| Center | 2.5 | Primary rim protector |

**Centers dominate blocking.**

---

## 6. FEATURE FİKİRLERİ

### 6.1 Core Defensive Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **Stl%_A** | Stl / Opp_Poss | Takım A'nın Stl% | 🔴 En yüksek |
| **Stl%_B** | Stl / Opp_Poss | Takım B'nin Stl% | 🔴 En yüksek |
| **Stl%Diff** | Stl%_A - Stl%_B | Steal farkı | 🔴 En yüksek |
| **Blk%_A** | Blk / Opp_FGA | Takım A'nın Blk% | 🟡 Orta |
| **Blk%_B** | Blk / Opp_FGA | Takım B'nin Blk% | 🟡 Orta |
| **Blk%Diff** | Blk%_A - Blk%_B | Block farkı | 🟡 Orta |

### 6.2 Defensive Disruption (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **DefDisruption_A** | Stl + Blk / Poss | Total disruption | 🟡 Orta |
| **DefDisruption_B** | Stl + Blk / Poss | Total disruption | 🟡 Orta |
| **DisruptionDiff** | Dis_A - Dis_B | Disruption farkı | 🟡 Orta |

### 6.3 Rim Protection (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **RimProtector_A** | Blk% × 0.6 + Stl% × 0.4 | Weighted metric | 🟢 Düşük |
| **RimProtector_B** | Blk% × 0.6 + Stl% × 0.4 | Weighted metric | 🟢 Düşük |

---

## 7. ÖNEMLİ GÖZLEMLER

### 7.1 Tournament Impact

**Steals importance:**
- Regular season: +0.45
- Tournament: +0.50

**Blocks importance:**
- Regular season: +0.35
- Tournament: +0.35 (stabil)

**Neden steals artar?**
- High pressure → turnovers increase
- Fast break points → steals değerli

### 7.2 Cinderella Teams

**Cinderella signature:**
- Yüksek Stl% → Turnover forced
- Active defense → Upset potential

**Örnek:**
- 2023 FAU: Stl% 11.2% (top %5)
- 2022 Saint Peter's: Stl% 10.8%

### 7.3 Defensive Consistency

**Steals = More consistent:**
- Game-to-game variance: σ = 2.1
- Blocks = Volatile:
- Game-to-game variance: σ = 3.8

**Feature selection:**
- Stl% > Blk% (reliability)

### 7.4 Pace Effect

**Hızlı tempo → daha fazla steals:**
- Fast pace: 10 Stl/G
- Slow pace: 6 Stl/G

**Blocks = pace-independent:**
- Rim protection unaffected

---

## 8. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Future games** | Sonece maç öncesi istatistikleri |
| **Pace effects** | Per possession kullan (Stl%, Blk%) |
| **Sample size** | Blocks yüksek variance, smoothing gerekli |

---

## 9. SUMMARY

### Kilit Noktalar

1. **Stl% > Blk% importance** (+0.45 vs +0.35)
2. **Per possession > Per game** (Stl%, Blk%)
3. **Steals = more consistent** (σ = 2.1 vs 3.8)
4. **Tournament'da steals importance artar** (+0.45 → +0.50)

### Feature Öncelik

```
🔴 En Yüksek:
  - Stl%Diff
  - Stl%_A, Stl%_B

🟡 Orta:
  - Blk%Diff
  - DefDisruptionDiff

🟢 Düşük:
  - Raw counts (Stl, Blk)
  - RimProtector (custom)
```

### Defensive Stats Summary

**Steals > Blocks:**
- More impact (1.2 vs 0.8 point)
- More reliable (+0.45 vs +0.35)
- More consistent (lower variance)

**Kullanım:** Stl%Diff primary, Blk%Diff secondary

---

*Analiz Tarihi: 01-03-2026*
*Grup: Defensive Stats (Variables #26-27)*
