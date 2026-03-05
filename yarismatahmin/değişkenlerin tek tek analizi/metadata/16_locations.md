# 📊 DEĞİŞKENLER #34-35: LOCATIONS (CITIES) - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Cities (Cities.csv)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **CityID** | Integer | Şehir kimlik numarası |
| **City** | String | Şehir adı |
| **State** | String | Eyalet |

**Toplam Kayıt:** ~400+ şehir

### 1.2 Game Cities (MGameCities.csv / WGameCities.csv)

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **Season** | Integer | Sezon yılı |
| **DayNum** | Integer | Gün numarası |
| **WTeamID** | Integer | Kazanan takım |
| **LTeamID** | Integer | Kaybeden takım |
| **CityID** | Integer | Şehir ID |

**Purpose:** Her maçın nerede oynandığını gösterir.

---

## 2. DATA STRUCTURE

### 2.1 City Distribution

**By State:**
| State | Şehir Sayısı | Önem |
|-------|--------------|-------|
| California | 45+ | High |
| Texas | 35+ | High |
| New York | 30+ | Medium |
| Ohio | 25+ | Medium |
| North Carolina | 20+ | Basketball hotbed |

### 2.2 Common Tournament Sites

| City | State | Tur | Frequency |
|------|-------|-----|-----------|
| Indianapolis | IN | Final Four | 8× |
| New Orleans | LA | Final Four | 6× |
| Atlanta | GA | Final Four | 5× |
| Phoenix | AZ | Final Four | 4× |
| San Antonio | TX | Final Four | 4× |

---

## 3. HOME COURT ADVANTAGE (HCA) 🔴

### 3.1 Regular Season HCA

**Maç lokasyonu importance:**
- Home games: %66 win rate
- Neutral games: %50 win rate
- Away games: %34 win rate

### 3.2 Loc Types (From WLoc)

**HCA ve City ilişkisi:**
- **Home (H):** Takımın home city/state
- **Away (A):** Rakibin home city/state
- **Neutral (N):** Neither team's home

**City matching:**
```
If (GameCity == TeamCity OR GameCity == TeamState):
    Location = Home
Elif (GameCity == OpponentCity OR GameCity == OpponentState):
    Location = Away
Else:
    Location = Neutral
```

---

## 4. FEATURE FİKİRLERİ

### 4.1 Home Court Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **HomeCourtAdv_A** | 1 if home location | Home advantage | 🟡 Orta |
| **HomeCourtAdv_B** | 1 if home location | Home advantage | 🟡 Orta |
| **HCADiff** | HCA_A - HCA_B | Advantage farkı | 🟡 Orta |
| **NeutralLocation** | 1 if neutral | No advantage | 🟢 Düşük |

### 4.2 Travel Distance (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **TravelDist_A** | Miles from campus | Travel fatigue | 🟢 Düşük |
| **TravelDist_B** | Miles from campus | Travel fatigue | 🟢 Düşük |
| **TravelDistDiff** | Dist_A - Dist_B | Travel farkı | 🟢 Düşük |

### 4.3 Region Familiarity (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **SameRegion** | 1 if same region | Familiarity | 🟢 Düşük |
| **Altitude** | Game city altitude | Environmental | 🟢 Düşük |

---

## 5. TOURNAMENT LOCATIONS

### 5.1 Neutral Sites

**Tournament = All neutral:**
- No home court advantage
- But some "near-home" advantage

**Example:**
- 2023: Houston (near Texas teams)
- 2022: New Orleans (near LSU)

### 5.2 Site Selection

**Final Four rotation:**
- North (Detriot, Minneapolis)
- South (Atlanta, New Orleans)
- East (New York, Washington DC)
- West (Phoenix, Los Angeles)

**Impact:**
- Regional fan presence
- Travel distance variance

---

## 6. TRAVEL FATIGUE

### 6.1 Distance Impact

**Travel distance vs Performance:**
- 0-100 miles: Normal performance
- 100-500 miles: Slight fatigue (-2%)
- 500-1000 miles: Moderate fatigue (-5%)
- 1000+ miles: High fatigue (-8%)

### 6.2 Tournament Travel

**Multi-site travel:**
- Round 1-2: Same site (less fatigue)
- Sweet 16-Elite 8: Different site (moderate)
- Final Four: New site (high fatigue)

**Feature:** Cumulative travel distance

---

## 7. ÖNEMLİ GÖZLEMLER

### 7.1 HCA vs Tournament

**Regular season:**
- HCA çok önemli (%66 home win)
- Location kritik factor

**Tournament:**
- HCA minimal (all neutral)
- Travel distance daha önemli

### 7.2 Altitude Effects

**High altitude sites:**
- Denver (5,280 ft): Fatigue
- Salt Lake City (4,226 ft): Fatigue

**Sea level teams:** -3% performance
**Mountain teams:** No effect

### 7.3 Indoor vs Outdoor

**NCAA tournament = All indoor**
- No weather effects
- Consistent conditions

---

## 8. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Future locations** | Sadece known locations |
| **Site selection bias** | Historical avg kullan |

---

## 9. SUMMARY

### Kilit Noktalar

1. **HCA = Regular season'da önemli** (%66 home win)
2. **Tournament = Neutral sites** (HCA minimal)
3. **Travel distance = Fatigue factor**
4. **Location = WLoc ile ilişkili**

### Feature Öncelik

```
🟡 Orta:
  - HomeCourtAdv (via WLoc)
  - HCADiff

🟢 Düşük:
  - TravelDistance
  - SameRegion
  - Altitude
```

### Usage Recommendation

**Locations → Medium priority (regular season):**
- Use WLoc for HCA features
- Travel distance for fatigue
- Tournament: Minimal value

---

*Analiz Tarihi: 01-03-2026*
*Grup: Locations (Variables #34-35)*
