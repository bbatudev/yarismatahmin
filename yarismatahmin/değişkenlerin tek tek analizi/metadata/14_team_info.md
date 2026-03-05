# 📊 DEĞİŞKENLER #29-30: TEAM INFO - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Team Names

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **TeamID** | Integer | Takım kimlik numarası (primary key) |
| **TeamName** | String | Takım adı |

**Dosyalar:**
- MTeams.csv (Erkek)
- WTeams.csv (Kadın)

**Toplam Takım:** ~400 aktif takım (her sezonda)

### 1.2 Team Spellings

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **TeamNameSpelling** | String | Alternatif isimler |
| **TeamID** | Integer | Doğru TeamID |

**Dosya:** MTeamSpellings.csv (W için de var)

**Purpose:** Data cleaning, external data matching

---

## 2. DATA STRUCTURE

### 2.1 Team ID Distribution

```
TeamID Range: 1101-1466 (Erkek)

Historical teams (inactive):
├── 1101-1200: Early era (1985-2000)
├── 1201-1300: Expansion era (2000-2010)
├── 1301-1400: Modern era (2010-2020)
└── 1401-1466: Recent additions (2020+)
```

### 2.2 Team Name Examples

| TeamID | TeamName | Konferans | Not |
|--------|----------|-----------|-----|
| 1181 | North Carolina | ACC | Blue Blood |
| 1231 | Duke | ACC | Blue Blood |
| 1246 | Kansas | B12 | Blue Blood |
| 1276 | Kentucky | SEC | Blue Blood |
| 1339 | Villanova | BE | Recent champ |
| 1396 | Baylor | B12 | Recent champ |

**Blue Blood = Tarihsel güçlü takımlar**

---

## 3. NAME VARIATIONS

### 3.1 Common Misspellings

| Doğru | Yanlışlar |
|-------|-----------|
| North Carolina | UNC, No Carolina, N. Carolina |
| Duke | Dook, Duk |
| Kentucky | UK, KY |
| Villanova | Nova, Villanova U |
| UCLA | UC Los Angeles, Cal-LA |

### 3.2 Abbreviations

| Full | Abbreviation |
|------|--------------|
| North Carolina | UNC |
| Duke | - |
| Kentucky | UK |
| UCLA | - |
| USC | Southern Cal |

### 3.3 Data Cleaning Importance

**External data integration:**
- News articles → Spellings to match
- Social media → Standardize names
- Historical data → ID matching

---

## 4. FEATURE FİKİRLERİ

### 4.1 Team ID NOT a Feature ❌

| Feature | Önem | Açıklama |
|---------|-------|----------|
| **TeamID** | ❌ None | Just an identifier |

**TeamID kullanma:**
- Numeric value meaningless
- No predictive power
- Only for merging data

### 4.2 Team History (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **HistoricalWin%** | All-time wins / games | Program success | 🟢 Düşük |
| **ChampionshipCount** | Total championships | History | 🟢 Düşük |
| **RecentSuccess** | Last 10 years | Modern era | 🟢 Düşük |

### 4.3 Blue Blood Indicator (Düşük Önem) 🟢

| Feature | Açıklama | Önem |
|---------|----------|------|
| **BlueBlood_A** | 1 if historical power | 🟢 Düşük |
| **BlueBlood_B** | 1 if historical power | 🟢 Düşük |

**Blue Blood teams:** UNC, Duke, Kansas, Kentucky, UCLA, Indiana

---

## 5. NAME SPELLINGS KULLANIMI

### 5.1 External Data Matching

**Senaryo:** Twitter data scraping

```
Raw tweet: "Go dook! #dukebasketball"

Process:
1. Tokenize: "dook", "dukebasketball"
2. Match: MTeamSpellings.csv
3. Result: TeamID = 1231 (Duke)
4. Feature: Duke social sentiment
```

### 5.2 News Article Analysis

**Senaryo:** ESPN article scraping

```
Article: "North Carolina beats Duke"

Process:
1. Extract: "North Carolina", "Duke"
2. Match: MTeamSpellings.csv
3. Result: TeamID 1181 vs 1231
4. Feature: Media coverage
```

### 5.3 Data Cleaning Pipeline

```
Raw Data → Spellings Match → TeamID → Merge → Features
```

**Critical step:** TeamID = primary key for all joins

---

## 6. ÖNEMLİ GÖZLEMLER

### 6.1 Team Name Consistency

**Problem:** Same team, different names
- Solution: Always use TeamID for joins
- Names: Only for display

### 6.2 Inactive Teams

**Some teams no longer exist:**
- Conference realignment
- School mergers
- Program discontinuation

**Solution:**
- Use active teams only
- Or handle inactive separately

### 6.3 Gender-Specific Files

**Erkek vs Kadın:**
- MTeams.csv vs WTeams.csv
- Different TeamIDs (overlapping possible)
- Separate analyses

---

## 7. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **TeamID as feature** | ❌ ASLA kullanma |
| **Historical bias** | Recent data weight daha fazla |
| **Future knowledge** | Historical stats → test set'te leakage |

---

## 8. SUMMARY

### Kilit Noktalar

1. **TeamID = Primary key, not a feature**
2. **TeamName = Display only**
3. **TeamSpellings = Data cleaning tool**
4. **Blue Blood = Historical context, low importance**

### Feature Öncelik

```
❌ Kullanma:
  - TeamID (identifier only)
  - TeamName (display only)

🟢 Düşük (Context):
  - HistoricalWin%
  - BlueBlood indicator
  - ChampionshipCount
```

### Usage Recommendation

**Team Info → Low priority:**
- TeamID only for data merging
- Names for human readability
- Spellings for external data
- Historical features: Minimal value

---

*Analiz Tarihi: 01-03-2026*
*Grup: Team Info (Variables #29-30)*
