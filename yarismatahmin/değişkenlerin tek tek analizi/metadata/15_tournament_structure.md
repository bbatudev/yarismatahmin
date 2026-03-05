# 📊 DEĞİŞKENLER #31-33: TOURNAMENT STRUCTURE - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Season Metadata (Seasons.csv)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **Season** | Integer | Sezon yılı |
| **DayZero** | Date | Sezon başı referans tarihi |
| **RegionW** | String | West bölge şampiyonu |
| **RegionX** | String | Midwest (X) bölge şampiyonu |
| **RegionY** | String | South (Y) bölge şampiyonu |
| **RegionZ** | String | East (Z) bölge şampiyonu |

**DayZero:** Sezonun ilk günü. DayNum hesabı için referans.

### 1.2 Tournament Slots (MNCAATourneySlots.csv)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **Season** | Integer | Sezon yılı |
| **Slot** | String | Eşleşme yeri (R1W1, R2WX1 vb.) |
| **StrongSeed** | String | Kazanan beklenen takım |
| **WeakSeed** | String | Kaybeden beklenen takım |

**Slot naming convention:**
- R1W1 = Round 1, West bracket, game 1
- R2WX1 = Round 2, Winner of X1
- R5WX = Round 5 (Final Four), Winner of X

### 1.3 Seed Round Slots (MNCAATourneySeedRoundSlots.csv)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **Seed** | String | Seed kodu (W01, X12 vb.) |
| **GameRound** | Integer | Tur numarası (0-6) |
| **GameSlot** | String | Maç slotu |
| **EarlyDayNum** | Integer | Erken oyun günü |
| **LateDayNum** | Integer | Geç oyun günü |

---

## 2. TOURNAMENT STRUCTURE

### 2.1 Bracket Layout

```
                    Final Four (R5)
                       /      \
              East (Z)       West (W)
              /    \          /    \
         Sweet 16       Sweet 16
         /  |   \       /  |   \
       R2  R2   R2     R2  R2   R2
```

**Rounds:**
- Round 0: First Four (DayNum 134-136)
- Round 1: First Round (DayNum 137-138)
- Round 2: Second Round (DayNum 139-140)
- Round 3: Sweet Sixteen (DayNum 144-145)
- Round 4: Elite Eight (DayNum 146-147)
- Round 5: Final Four (DayNum 151)
- Round 6: Championship (DayNum 152)

### 2.2 Seed Distribution

**Her region 16 seed:**
- 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16

**First Four:**
- 4x 16 vs 16 matchup (2 game)
- 4x 11 vs 11 matchup (2 game)

**Total:** 68 takım → 67 maç

### 2.3 Region Names

| Kod | Region Bölge |
|-----|-------------|
| W | West |
| X | Midwest |
| Y | South |
| Z | East |

---

## 3. FEATURE FİKİRLERİ

### 3.1 Tournament Path Features (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **PathStrength_A** | Avg seed of opponents | Turnuva yolu zorluğu | 🟢 Düşük |
| **PathStrength_B** | Avg seed of opponents | Turnuva yolu zorluğu | 🟢 Düşük |
| **RegionW_A** | 1 if West region | Region advantage | 🟢 Düşük |

### 3.2 First Four Impact (Düşük Önem) 🟢

| Feature | Açıklama | Önem |
|---------|----------|------|
| **FirstFour_A** | 1 if played First Four | Fatigue | 🟢 Düşük |
| **FirstFour_B** | 1 if played First Four | Fatigue | 🟢 Düşük |
| **ExtraGame** | 1 if played extra game | Disadvantage | 🟢 Düşük |

### 3.3 Location Features (Düşük Önem) 🟢

| Feature | Açıklama | Önem |
|---------|----------|------|
| **HomeRegion** | 1 if home state region | Home court | 🟢 Düşük |
| **TravelDistance** | Miles to game site | Travel fatigue | 🟢 Düşük |

---

## 4. BRACKET MISMATCH

### 4.1 Seed vs Mismatch

**Senaryo:** Two 1 seeds in same region → impossible

**Slot matching:**
```
Region W:
  R1W1: W01 vs W16
  R1W2: W08 vs W09
  R2WX1: Winner of R1W1 vs Winner of R1W2
```

### 4.2 Potential Matchups

**Early round projection:**
```
Seed 1 vs Seed 16: Round 1
Seed 1 vs Seed 8/9: Round 2
Seed 1 vs Seed 4/5: Round 3
Seed 1 vs Seed 2/3: Round 4
```

**Feature:** Seed matchups predictable in early rounds

---

## 5. ÖNEMLİ GÖZLEMLER

### 5.1 Final Four Path

**Typical path (1 seed):**
- R1: +16 (easy)
- R2: +8/9 (medium)
- R3: +4/5 (hard)
- R4: +2/3 (very hard)
- R5: 1/2/3 (elite)

**Cinderella path (11 seed):**
- R1: -6 (upset)
- R2: -3/14 (medium)
- R3: +2/15 (hard)
- R4: +1/10 (very hard)

### 5.2 Region Balance

**Her region roughly equal strength:**
- Selection committee ensures balance
- But slight variations exist

**Feature:** RegionStrength (historical)

### 5.3 First Four Disadvantage

**First Four teams:**
- Extra game → fatigue
- Less preparation time
- Historical win%: %35 vs %45 (normal)

---

## 6. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Future matchups** | Sadece possible matchups |
| **Region winners** | Don't use RegionW/X/Y/Z |
| **Champion knowledge** | Known only after tournament |

---

## 7. SUMMARY

### Kilit Noktalar

1. **Tournament structure = Predictable brackets**
2. **Slots = Future matchups (handle carefully)**
3. **First Four = Disadvantage**
4. **Region = Minimal advantage**

### Feature Öncelik

```
🟢 Düşük (Context):
  - PathStrength
  - FirstFour indicator
  - Region indicator
  - TravelDistance

❌ Kullanma:
  - RegionW/X/Y/Z (champion info)
  - Future slot matchups
```

### Usage Recommendation

**Tournament Structure → Very low priority:**
- Mostly organizational data
- Some contextual features possible
- Don't use winner information

---

*Analiz Tarihi: 01-03-2026*
*Grup: Tournament Structure (Variables #31-33)*
